from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

print("=" * 60)
print("P10-5 DEEP DIAGNOSTIC")
print("DO NOT MODIFY MAIN.PY")
print("=" * 60)

src = MAIN.read_text(encoding="utf-8-sig")
tree = ast.parse(src, filename=str(MAIN))
lines = src.splitlines()

def show_range(start, end, title):
    print("\n" + "=" * 60)
    print(title)
    print(f"LINES {start}-{end}")
    print("=" * 60)
    for i in range(max(1, start), min(len(lines), end) + 1):
        print(f"{i:5}: {lines[i-1]}")

# ------------------------------------------------------------
# 1. Locate MINH class
# ------------------------------------------------------------
minh_class = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "MINH":
        minh_class = node
        break

if minh_class is None:
    print("MINH CLASS: FAIL")
    raise SystemExit(1)

print("MINH CLASS: PASS")
print(f"MINH CLASS RANGE: {minh_class.lineno}-{minh_class.end_lineno}")

# ------------------------------------------------------------
# 2. Locate __init__
# ------------------------------------------------------------
init_node = None

for node in minh_class.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "__init__":
            init_node = node
            break

if init_node is None:
    print("MINH.__init__: FAIL")
else:
    print("MINH.__init__: PASS")
    print(f"INIT RANGE: {init_node.lineno}-{init_node.end_lineno}")

    # Show every self.xxx assignment in __init__
    attrs = []

    for node in ast.walk(init_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attrs.append(target.attr)

        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                attrs.append(target.attr)

    attrs = sorted(set(attrs))

    print("\nSELF ATTRIBUTES IN __init__:")
    for attr in attrs:
        print("  self." + attr)

    for wanted in ["risk", "simulator", "judge"]:
        print(
            f"\nINIT ATTRIBUTE {wanted}: "
            + ("FOUND" if wanted in attrs else "MISSING")
        )

# ------------------------------------------------------------
# 3. Locate P10-related functions
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10 FUNCTIONS / METHODS")
print("=" * 60)

p10_nodes = []

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = node.name.lower()
        if "p10" in name or "risk" in name or "simulator" in name or "judge" in name:
            p10_nodes.append(node)

for node in sorted(p10_nodes, key=lambda x: x.lineno):
    print(
        f"{node.lineno:5}-{node.end_lineno:<5} "
        f"{node.name}"
    )

# ------------------------------------------------------------
# 4. Find exact P10 imports
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10 IMPORTS")
print("=" * 60)

for node in tree.body:
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name in ("risk", "simulator", "judge"):
                print(
                    f"LINE {node.lineno}: "
                    f"import {alias.name}"
                    + (f" as {alias.asname}" if alias.asname else "")
                )

    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if module in ("risk", "simulator", "judge"):
            names = ", ".join(
                f"{a.name}" + (f" as {a.asname}" if a.asname else "")
                for a in node.names
            )
            print(f"LINE {node.lineno}: from {module} import {names}")

# ------------------------------------------------------------
# 5. Find ALL occurrences of risk/simulator/judge
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("ALL P10 SOURCE OCCURRENCES")
print("=" * 60)

keywords = ("risk", "simulator", "judge")

for i, line in enumerate(lines, 1):
    low = line.lower()
    if any(k in low for k in keywords):
        print(f"{i:5}: {line}")

# ------------------------------------------------------------
# 6. Locate P10 evaluation call
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10 EVALUATION CALLS")
print("=" * 60)

calls = []

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func = node.func

        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            name = ""

        if "p10" in name.lower() or "evaluation" in name.lower():
            calls.append((node.lineno, name))

for line_no, name in sorted(set(calls)):
    print(f"LINE {line_no}: CALL {name}")

# ------------------------------------------------------------
# 7. Show exact MINH.process section around P10
# ------------------------------------------------------------
process_node = None

for node in minh_class.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "process":
            process_node = node
            break

if process_node:
    print("\nPROCESS RANGE:")
    print(process_node.lineno, "-", process_node.end_lineno)

    p10_lines = []

    for i in range(process_node.lineno, process_node.end_lineno + 1):
        low = lines[i-1].lower()
        if any(k in low for k in keywords) or "p10" in low:
            p10_lines.append(i)

    if p10_lines:
        start = max(process_node.lineno, min(p10_lines) - 15)
        end = min(process_node.end_lineno, max(p10_lines) + 35)
        show_range(
            start,
            end,
            "MINH.process() — P10 CONTEXT"
        )
    else:
        print("NO P10 TEXT FOUND INSIDE PROCESS")

# ------------------------------------------------------------
# 8. Show __init__ around likely insertion area
# ------------------------------------------------------------
if init_node:
    show_range(
        max(1, init_node.lineno),
        min(init_node.end_lineno, init_node.lineno + 260),
        "MINH.__init__ — FIRST 260 LINES"
    )

# ------------------------------------------------------------
# 9. Static verdict
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("DIAGNOSTIC VERDICT")
print("=" * 60)

has_risk_self = any(
    isinstance(n, ast.Attribute)
    and isinstance(n.value, ast.Name)
    and n.value.id == "self"
    and n.attr == "risk"
    for n in ast.walk(tree)
)

has_sim_self = any(
    isinstance(n, ast.Attribute)
    and isinstance(n.value, ast.Name)
    and n.value.id == "self"
    and n.attr == "simulator"
    for n in ast.walk(tree)
)

has_judge_self = any(
    isinstance(n, ast.Attribute)
    and isinstance(n.value, ast.Name)
    and n.value.id == "self"
    and n.attr == "judge"
    for n in ast.walk(tree)
)

print("ANY self.risk:", "FOUND" if has_risk_self else "MISSING")
print("ANY self.simulator:", "FOUND" if has_sim_self else "MISSING")
print("ANY self.judge:", "FOUND" if has_judge_self else "MISSING")

print("\nNO FILE WAS MODIFIED.")
print("=" * 60)
