from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"

print("=" * 60)
print("P10-5 DEEP DIAGNOSTIC V2")
print("READ ONLY — MAIN.PY WILL NOT BE MODIFIED")
print("=" * 60)

src = MAIN.read_text(encoding="utf-8-sig")
lines = src.splitlines()
tree = ast.parse(src, filename=str(MAIN))

def show(start, end, title):
    print("\n" + "=" * 60)
    print(title)
    print(f"LINES {start}-{end}")
    print("=" * 60)
    for i in range(max(1, start), min(len(lines), end) + 1):
        print(f"{i:5}: {lines[i-1]}")

# ------------------------------------------------------------
# 1. Find MINH class ANYWHERE in AST
# ------------------------------------------------------------
classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
]

print(f"\nAST CLASSES FOUND: {len(classes)}")

for c in classes:
    print(f"  {c.name}: {c.lineno}-{c.end_lineno}")

minh_classes = [c for c in classes if c.name == "MINH"]

if not minh_classes:
    print("\nMINH CLASS: NOT FOUND")
else:
    print("\nMINH CLASS: PASS")
    minh = minh_classes[0]
    print(f"MINH RANGE: {minh.lineno}-{minh.end_lineno}")

    # --------------------------------------------------------
    # 2. Find __init__ and process
    # --------------------------------------------------------
    methods = [
        n for n in minh.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    print("\nMINH METHODS:")
    for m in methods:
        print(f"  {m.name}: {m.lineno}-{m.end_lineno}")

    init = next((m for m in methods if m.name == "__init__"), None)
    process = next((m for m in methods if m.name == "process"), None)

    # --------------------------------------------------------
    # 3. __init__ self attributes
    # --------------------------------------------------------
    if init:
        attrs = set()

        for n in ast.walk(init):
            if isinstance(n, ast.Assign):
                targets = n.targets
            elif isinstance(n, ast.AnnAssign):
                targets = [n.target]
            else:
                continue

            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attrs.add(target.attr)

        print("\n__init__ SELF ATTRIBUTES:")
        for a in sorted(attrs):
            print("  self." + a)

        print("\nP10 __init__ CHECK:")
        for a in ("risk", "simulator", "judge"):
            print(
                f"  self.{a}: "
                + ("FOUND" if a in attrs else "MISSING")
            )

    # --------------------------------------------------------
    # 4. All self.risk / simulator / judge references
    # --------------------------------------------------------
    print("\nALL self.risk / self.simulator / self.judge REFERENCES:")

    refs = []

    for n in ast.walk(minh):
        if isinstance(n, ast.Attribute):
            if (
                isinstance(n.value, ast.Name)
                and n.value.id == "self"
                and n.attr in ("risk", "simulator", "judge")
            ):
                refs.append((n.lineno, f"self.{n.attr}"))

    if refs:
        for line_no, value in sorted(set(refs)):
            print(f"  {line_no}: {value}")
    else:
        print("  NONE")

# ------------------------------------------------------------
# 5. Find every P10 function
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10-RELATED FUNCTIONS")
print("=" * 60)

for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = n.name.lower()
        if (
            "p10" in name
            or "risk" in name
            or "simulator" in name
            or "judge" in name
        ):
            print(f"{n.lineno:5}-{n.end_lineno:<5} {n.name}")

# ------------------------------------------------------------
# 6. Find P10-related source lines
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10 SOURCE REFERENCES")
print("=" * 60)

for i, line in enumerate(lines, 1):
    low = line.lower()

    if (
        "risk" in low
        or "simulator" in low
        or "judge" in low
        or "p10" in low
    ):
        print(f"{i:5}: {line}")

# ------------------------------------------------------------
# 7. Find process by AST
# ------------------------------------------------------------
process_nodes = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    and n.name == "process"
]

print("\n" + "=" * 60)
print("PROCESS METHODS")
print("=" * 60)

for p in process_nodes:
    print(f"process: {p.lineno}-{p.end_lineno}")

if process_nodes:
    p = process_nodes[0]

    relevant = []

    for i in range(p.lineno, p.end_lineno + 1):
        low = lines[i - 1].lower()

        if (
            "risk" in low
            or "simulator" in low
            or "judge" in low
            or "p10" in low
        ):
            relevant.append(i)

    if relevant:
        start = max(p.lineno, min(relevant) - 20)
        end = min(p.end_lineno, max(relevant) + 40)

        show(
            start,
            end,
            "PROCESS() P10 CONTEXT"
        )
    else:
        print("NO P10 REFERENCES INSIDE PROCESS")

# ------------------------------------------------------------
# 8. Exact class/module structure around MINH
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("TOP-LEVEL STRUCTURE")
print("=" * 60)

for n in tree.body:
    name = getattr(n, "name", "")
    print(
        f"{n.lineno:5}-{getattr(n, 'end_lineno', n.lineno):<5} "
        f"{type(n).__name__:<15} {name}"
    )

# ------------------------------------------------------------
# 9. Detect P10 state attributes
# ------------------------------------------------------------
print("\n" + "=" * 60)
print("P10 STATE ATTRIBUTES IN SOURCE")
print("=" * 60)

state_names = (
    "last_p10_evaluation",
    "last_p10_risk",
    "last_p10_simulation",
    "last_p10_judgement",
    "last_p10_judge",
)

for name in state_names:
    hits = []

    for i, line in enumerate(lines, 1):
        if name in line:
            hits.append(i)

    if hits:
        print(f"{name}: FOUND at {hits}")
    else:
        print(f"{name}: NOT FOUND")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("NO FILE WAS MODIFIED")
print("=" * 60)
