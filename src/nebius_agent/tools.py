"""Tools for the reference agent: a price lookup and a safe calculator.

The question "what do 8 H200s for 72 hours cost?" needs both, in order, which
exercises a multi-step tool loop rather than a single call.
"""
import ast
import operator

from langchain_core.tools import tool

# Illustrative numbers for the demo only. NOT real Nebius pricing.
_MOCK_GPU_PRICES_USD_PER_HOUR = {
    "H100": 2.95,
    "H200": 3.50,
    "B200": 5.50,
    "L40S": 1.55,
}

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


@tool
def get_gpu_price(gpu_type: str) -> str:
    """Look up the on-demand price per GPU-hour in USD for a GPU type such as H100, H200, B200 or L40S."""
    key = gpu_type.strip().upper().removeprefix("NVIDIA ")
    if key not in _MOCK_GPU_PRICES_USD_PER_HOUR:
        return f"Unknown GPU type '{gpu_type}'. Known types: {', '.join(_MOCK_GPU_PRICES_USD_PER_HOUR)}."
    return f"{key}: ${_MOCK_GPU_PRICES_USD_PER_HOUR[key]:.2f} per GPU-hour (mock price)"


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("only numbers and + - * / ** are allowed")


@tool
def calculate(expression: str) -> str:
    """Evaluate an arithmetic expression, e.g. '8 * 72 * 3.5'. Supports + - * / ** and parentheses."""
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


TOOLS = [get_gpu_price, calculate]
