import ast

path = "main.py"

with open(path, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

print("=== MAIN.PY METHOD MAP ===")

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [a.arg for a in node.args.args]
        has_self = bool(args and args[0] == "self")
        print(
            "METHOD:",
            node.name,
            "| lines:",
            node.lineno,
            "-",
            getattr(node, "end_lineno", node.lineno),
            "| self:",
            has_self,
        )

print("=== RESPONSE / EXECUTION MARKERS ===")

markers = [
    "RESPONSE GUARD",
    "return ",
    "last_execution_contract",
    "process(",
    "execute",
    "verify",
]

for i, line in enumerate(source.splitlines(), 1):
    if any(marker in line for marker in markers):
        print(f"{i}: {line}")

print("=== END ===")
