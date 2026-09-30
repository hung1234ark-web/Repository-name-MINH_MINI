

from __future__ import annotations

import ast
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

KEYWORDS = (
    "ollama",
    "chat",
    "generate",
    "completion",
    "qwen",
    "model",
    "api",
)


def scan_file(path: Path):
    try:
        source = path.read_text(encoding="utf-8-sig")
    except Exception:
        return

    lower = source.lower()

    matched_keywords = [
        keyword
        for keyword in KEYWORDS
        if keyword in lower
    ]

    if not matched_keywords:
        return

    print("=" * 70)
    print(f"FILE: {path.name}")
    print(f"KEYWORDS: {', '.join(matched_keywords)}")

    try:
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        print(f"AST ERROR: {type(exc).__name__}: {exc}")
        return

    found = False

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lower()

            related = (
                any(k in name for k in KEYWORDS)
                or any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr.lower() in {
                        "post",
                        "get",
                        "chat",
                        "generate",
                        "create",
                    }
                    for child in ast.walk(node)
                )
            )

            if related:
                found = True
                print(
                    f"  FUNCTION : {node.name}"
                    f"  | line {node.lineno}"
                )

                args = []

                for arg in node.args.posonlyargs:
                    args.append(arg.arg)

                for arg in node.args.args:
                    args.append(arg.arg)

                for arg in node.args.kwonlyargs:
                    args.append(arg.arg)

                if node.args.vararg:
                    args.append("*" + node.args.vararg.arg)

                if node.args.kwarg:
                    args.append("**" + node.args.kwarg.arg)

                print(
                    "             PARAMETERS:",
                    ", ".join(args),
                )

        elif isinstance(node, ast.ClassDef):
            name = node.name.lower()

            if any(k in name for k in KEYWORDS):
                found = True
                print(
                    f"  CLASS    : {node.name}"
                    f"  | line {node.lineno}"
                )

    if not found:
        print("  No obvious handler function/class found.")


def main():
    print("=" * 70)
    print("MINH MINI — CHAT / OLLAMA HANDLER DISCOVERY")
    print("=" * 70)
    print(f"SCAN: {BASE_DIR}")
    print()

    files = sorted(BASE_DIR.glob("*.py"))

    for path in files:
        if path.name == Path(__file__).name:
            continue

        scan_file(path)

    print()
    print("=" * 70)
    print("END DISCOVERY")
    print("=" * 70)


if __name__ == "__main__":
    main()