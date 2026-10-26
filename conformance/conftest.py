"""Run every conformance test against every model, then write a results matrix.

    uv run pytest                                   # default model set
    NEBIUS_TEST_MODELS="moonshotai/Kimi-K3" uv run pytest
"""
import os
import re
from collections import defaultdict
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODELS = [
    "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "moonshotai/Kimi-K3",
    "deepseek-ai/DeepSeek-V4.1-Flash",
    "zai-org/GLM-5.3",
    "openai/gpt-oss-120b",
    "meta-models/muse-spark-open",
    "google/gemma-3-27b-it",
]
MODELS = [m.strip() for m in os.getenv("NEBIUS_TEST_MODELS", ",".join(DEFAULT_MODELS)).split(",") if m.strip()]

CLIENT = os.getenv("NEBIUS_CLIENT", "chatopenai")  # "chatopenai" (our factory) or "langchain-nebius"

_results: dict[str, dict[str, str]] = defaultdict(dict)
_failures: list[str] = []


def pytest_generate_tests(metafunc):
    if "model" in metafunc.fixturenames:
        metafunc.parametrize("model", MODELS)


def pytest_runtest_logreport(report):
    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return
    m = re.match(r".*::(\w+)\[(.+)\]$", report.nodeid)
    if not m:
        return
    test, params = m.groups()
    model = next((x for x in MODELS if x in params), None)
    if not model:
        return
    extra = params.replace(model, "").strip("-")  # e.g. the structured-output method
    if extra:
        test = f"{test}[{extra}]"
    file = Path(report.nodeid.split("::")[0]).stem.removeprefix("test_")
    _results[f"{file}::{test}"][model] = {"passed": "✅", "failed": "❌", "skipped": "⚪"}[report.outcome]
    if report.failed:
        crash = getattr(report.longrepr, "reprcrash", None)
        message = (crash.message if crash else str(report.longrepr)).splitlines()[0][:220]
        _failures.append(f"- `{file}::{test}` · `{model}`: {message}")


def _provenance() -> list[str]:
    import datetime
    import importlib.metadata as md
    import subprocess
    import sys

    from nebius_agent.llm import NEBIUS_BASE_URL

    def git(*args):
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True, cwd=Path(__file__).parent).stdout.strip()
        except OSError:
            return ""

    dirty = git("status", "--porcelain", "--", ".", ":!conformance/results")  # ignore this run's own output
    commit = git("rev-parse", "--short", "HEAD") + (" (uncommitted changes)" if dirty else "")
    endpoint = NEBIUS_BASE_URL
    if CLIENT == "langchain-nebius":
        from langchain_nebius import ChatNebius

        endpoint = ChatNebius(model="x", api_key="unused").nebius_api_base + " (package default)"
    packages = ["langchain-core", "langchain-openai", "langgraph", "openai"] + (["langchain-nebius"] if CLIENT == "langchain-nebius" else [])
    versions = []
    for p in packages:
        try:
            versions.append(f"{p}=={md.version(p)}")
        except md.PackageNotFoundError:
            pass
    return [
        f"- **Date (UTC):** {datetime.datetime.now(datetime.UTC):%Y-%m-%d %H:%M}",
        f"- **Client:** `{CLIENT}`",
        f"- **Commit:** `{commit}`",
        f"- **Endpoint:** `{endpoint}`",
        f"- **Packages:** {', '.join(f'`{v}`' for v in versions)}",
        f"- **Command:** `pytest {' '.join(sys.argv[1:])}`" + (f" with `NEBIUS_CLIENT={CLIENT}`" if CLIENT != "chatopenai" else ""),
        f"- **Models:** {', '.join(f'`{m}`' for m in MODELS)}",
    ]


def pytest_sessionfinish(session):
    if not _results:
        return
    models = [m for m in MODELS if any(m in r for r in _results.values())]
    lines = [
        f"# Conformance results: `{CLIENT}` client on Token Factory",
        "",
        *_provenance(),
        "",
        "✅ pass · ❌ fail · ⚪ skipped",
        "",
        "| test | " + " | ".join(m.split("/")[-1] for m in models) + " |",
        "|---|" + "---|" * len(models),
    ]
    for test in sorted(_results):
        lines.append(f"| `{test}` | " + " | ".join(_results[test].get(m, "") for m in models) + " |")
    if _failures:
        lines += ["", "## Failure details", "", *sorted(_failures)]
    out = Path(__file__).parent / "results" / f"{CLIENT}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"\nconformance matrix written to {out}")


@pytest.fixture
def llm(model):
    # NEBIUS_CLIENT=langchain-nebius runs the same checks against the official ChatNebius package
    if os.getenv("NEBIUS_CLIENT") == "langchain-nebius":
        from langchain_nebius import ChatNebius

        return ChatNebius(model=model, temperature=0, max_tokens=1024)
    from nebius_agent.llm import make_chat_model

    return make_chat_model(model, max_tokens=1024)
