from pathlib import Path

p = Path("apply_p9_8.py")
s = p.read_text(encoding="utf-8-sig")

old = '''old = """        if isinstance(tasks, list) and tasks:
            checks["plan_has_execution_path"] = True
        else:
            checks["plan_has_execution_path"] = False
            checks["simple_goal_without_plan"] = True
"""'''

new = '''old = """        if isinstance(tasks, list) and tasks:
            checks["plan_has_execution_path"] = True
        else:
            warnings.append(
                "no_clear_execution_path"
            )
            checks[
                "plan_has_execution_path"
            ] = False
"""'''

replacement = '''new = """        if isinstance(tasks, list) and tasks:
            checks["plan_has_execution_path"] = True
        else:
            checks[
                "plan_has_execution_path"
            ] = False
            checks["simple_goal_without_plan"] = True
"""'''

if old not in s:
    raise RuntimeError("P9-8 RED TEAM PATCH ANCHOR NOT FOUND")

s = s.replace(old, replacement, 1)

p.write_text(s, encoding="utf-8-sig")

print("P9-8 RED TEAM EXECUTION-PATH PATCH: PASS")
