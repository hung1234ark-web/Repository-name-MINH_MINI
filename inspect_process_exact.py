from pathlib import Path
import ast

p = Path("main.py")
source = p.read_text(encoding="utf-8")
tree = ast.parse(source)

for node in ast.walk(tree):
    if (
        isinstance(node, ast.ClassDef)
        and node.name == "MinhMiniCore"
    ):
        for fn in node.body:
            if (
                isinstance(fn, ast.FunctionDef)
                and fn.name == "process"
            ):
                lines = source.splitlines()
                start = fn.lineno
                end = fn.end_lineno

                print("=== EXACT MinhMiniCore.process() ===")
                print(f"LINES: {start}-{end}")
                print()

                for i in range(start, end + 1):
                    print(
                        f"{i:04d}: {lines[i-1]}"
                    )

                print()
                print("=== END PROCESS ===")
                raise SystemExit(0)

raise SystemExit(
    "ERROR: Không tìm thấy MinhMiniCore.process()"
)
