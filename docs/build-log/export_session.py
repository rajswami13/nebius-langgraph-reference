"""Render a Claude Code session log (.jsonl) as a readable, redacted Markdown transcript.

    uv run python docs/build-log/export_session.py ~/.claude/projects/<project>/<session>.jsonl > docs/build-log/session.md

Kept: user messages, assistant replies, every tool call (tool, description, command or file),
and tool results truncated to RESULT_CHARS. Omitted: internal reasoning blocks, harness
bookkeeping records, and system reminders. Secrets are redacted (see REDACT).
"""
import json
import os
import re
import sys

RESULT_CHARS = 700
REDACT = [
    (re.compile(r"v1\.[A-Za-z0-9._\-]{20,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"gh[opsu]_[A-Za-z0-9]{10,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"Yqv89jCsskJbX7BV"), "[REDACTED_PROMO_CODE]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@gmail\.com"), "[REDACTED_EMAIL]"),
]
if os.getenv("NEBIUS_API_KEY"):
    REDACT.insert(0, (re.compile(re.escape(os.environ["NEBIUS_API_KEY"])), "[REDACTED_API_KEY]"))


def clean(text: str) -> str:
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    for pattern, repl in REDACT:
        text = pattern.sub(repl, text)
    return text.strip()


def short(text: str, n: int = RESULT_CHARS) -> str:
    return text if len(text) <= n else text[:n] + f"\n… [{len(text) - n} more characters]"


def tool_call(block: dict) -> str:
    inp = block.get("input", {})
    name = block["name"]
    desc = inp.get("description", "")
    detail = inp.get("command") or inp.get("file_path") or inp.get("query") or inp.get("url") or inp.get("skill") or ""
    head = f"**🔧 {name}**" + (f" · {desc}" if desc else "")
    if name in ("Write", "Edit"):
        size = len(inp.get("content") or inp.get("new_string") or "")
        return f"{head}\n\n`{detail}` ({size} characters written)"
    return f"{head}\n\n```\n{clean(str(detail))}\n```" if detail else head


def result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, list):
        content = "\n".join(c.get("text", "") for c in content if c.get("type") == "text")
    return clean(str(content or ""))


def main(path: str) -> None:
    out = [
        "# Build record: Claude Code session",
        "",
        "Rendered from the raw Claude Code session log by [export_session.py](export_session.py).",
        "Internal reasoning blocks and harness bookkeeping are omitted, tool results are truncated, and secrets are redacted.",
        "",
    ]
    for line in open(path):
        rec = json.loads(line)
        kind, msg = rec.get("type"), rec.get("message") or {}
        if kind not in ("user", "assistant"):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for block in content or []:
            t = block.get("type")
            if kind == "user" and t == "text":
                text = clean(block["text"])
                if text:
                    out += [f"---\n\n### 👤 User · {rec.get('timestamp', '')[:16]}", "", text, ""]
            elif kind == "user" and t == "document":
                title = (block.get("title") or block.get("source", {}).get("media_type", "document"))
                out += [f"*[User attached a document: {title}]*", ""]
            elif kind == "assistant" and t == "text":
                text = clean(block["text"])
                if text:
                    out += ["### 🤖 Claude", "", text, ""]
            elif kind == "assistant" and t == "tool_use":
                out += [tool_call(block), ""]
            elif kind == "user" and t == "tool_result":
                text = result_text(block)
                if text:
                    out += ["<details><summary>result</summary>", "", "```", short(text), "```", "", "</details>", ""]
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
