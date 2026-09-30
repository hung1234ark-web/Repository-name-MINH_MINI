from pathlib import Path
import ast

MAIN = Path("main.py")
SOURCE = MAIN.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

print("=== P4-5 EXECUTION_DECISION EXACT INSPECTION ===")

core = None

for node in TREE.body:
    if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
        core = node
        break

if core is None:
    raise RuntimeError("Không tìm thấy class MinhMiniCore")

execute_node = None

for node in core.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "execute_decision":
            execute_node = node
            break

if execute_node is None:
    raise RuntimeError(
        "Không tìm thấy MinhMiniCore.execute_decision()"
    )

source = ast.get_source_segment(
    SOURCE,
    execute_node,
)

if not source:
    raise RuntimeError(
        "Không đọc được source execute_decision()"
    )

print(
    f"LINES: "
    f"{execute_node.lineno}-"
    f"{getattr(execute_node, 'end_lineno', '?')}"
)

print("")
print("=== EXACT execute_decision() ===")
print(source)
print("")
print("=== END EXACT SOURCE ===")

print("")
print("=== RETURN ANALYSIS ===")

returns = [
    node
    for node in ast.walk(execute_node)
    if isinstance(node, ast.Return)
]

print("RETURN COUNT:", len(returns))

for index, node in enumerate(returns, 1):
    segment = ast.get_source_segment(
        SOURCE,
        node,
    )

    print("")
    print(f"RETURN #{index}:")
    print(segment)

print("")
print("=== P4-5 DIAGNOSTIC ONLY ===")
print("SOURCE MODIFIED: NO")
print("BACKUP CREATED: NO")
print("=== INSPECTION DONE ===")
