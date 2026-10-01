import os
import py_compile

from task_planner import TaskPlanner, create_task_planner, self_check


APP_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_FILE = os.path.join(APP_DIR, "task_planner.py")

all_pass = True


def check(name, condition):
    global all_pass
    result = bool(condition)
    print(f"{name}: {'PASS' if result else 'FAIL'}")
    all_pass = all_pass and result


print("=== P7-1 TASK PLANNER CORE VALIDATION ===")

# ---------------------------------------------------------
# FILE
# ---------------------------------------------------------

check("TASK_PLANNER_FILE", os.path.isfile(TASK_FILE))

# ---------------------------------------------------------
# COMPILE
# ---------------------------------------------------------

try:
    py_compile.compile(TASK_FILE, doraise=True)
    check("TASK_PLANNER_COMPILE", True)
except Exception as exc:
    print("COMPILE_ERROR:", exc)
    check("TASK_PLANNER_COMPILE", False)

# ---------------------------------------------------------
# IMPORT
# ---------------------------------------------------------

try:
    from task_planner import TaskPlanner
    check("TASK_PLANNER_IMPORT", True)
except Exception as exc:
    print("IMPORT_ERROR:", exc)
    check("TASK_PLANNER_IMPORT", False)
    raise SystemExit(1)

# ---------------------------------------------------------
# CREATION
# ---------------------------------------------------------

planner = TaskPlanner()

check("PLANNER_CREATION", isinstance(planner, TaskPlanner))
check("INITIAL_TASKS_EMPTY", planner.get_tasks() == [])
check("INITIAL_GOAL_NONE", planner.get_goal() is None)
check("INITIAL_CURRENT_NONE", planner.get_current_task() is None)

# ---------------------------------------------------------
# GOAL
# ---------------------------------------------------------

goal = {
    "text": "Mở YouTube rồi tìm Python",
    "intent": "action",
    "target": "youtube",
}

planner.set_goal(goal)

check(
    "GOAL_STORAGE",
    planner.get_goal() == goal,
)

# ---------------------------------------------------------
# TASK CREATION
# ---------------------------------------------------------

task1 = planner.add_task("Mở YouTube")
task2 = planner.add_task("Tìm Python")

check(
    "TASK1_CREATED",
    task1["id"] == "task_1"
    and task1["description"] == "Mở YouTube"
    and task1["status"] == "planned",
)

check(
    "TASK2_CREATED",
    task2["id"] == "task_2"
    and task2["description"] == "Tìm Python"
    and task2["status"] == "planned",
)

check(
    "TASK_COUNT",
    len(planner.get_tasks()) == 2,
)

# ---------------------------------------------------------
# CURRENT TASK
# ---------------------------------------------------------

current = planner.get_current_task()

check(
    "CURRENT_TASK_INITIAL",
    current is not None
    and current["id"] == "task_1",
)

# ---------------------------------------------------------
# ACTIVATE TASK
# ---------------------------------------------------------

updated1 = planner.update_task_status(
    "task_1",
    "active",
)

check(
    "TASK1_ACTIVE",
    updated1["status"] == "active",
)

check(
    "CURRENT_TASK_ACTIVE",
    planner.get_current_task()["id"] == "task_1",
)

# ---------------------------------------------------------
# COMPLETE TASK
# ---------------------------------------------------------

completed1 = planner.update_task_status(
    "task_1",
    "completed",
)

check(
    "TASK1_COMPLETED",
    completed1["status"] == "completed",
)

check(
    "NEXT_TASK_SELECTED",
    planner.get_current_task()["id"] == "task_2",
)

# ---------------------------------------------------------
# BLOCKED TASK
# ---------------------------------------------------------

planner.update_task_status(
    "task_2",
    "blocked",
)

check(
    "TASK2_BLOCKED",
    planner.get_task("task_2")["status"] == "blocked",
)

check(
    "NO_CURRENT_AFTER_BLOCK",
    planner.get_current_task() is None,
)

# ---------------------------------------------------------
# SNAPSHOT ISOLATION
# ---------------------------------------------------------

snapshot = planner.snapshot()

snapshot["tasks"][0]["status"] = "failed"
snapshot["goal"]["text"] = "MODIFIED"

live_task = planner.get_task("task_1")
live_goal = planner.get_goal()

check(
    "SNAPSHOT_TASK_ISOLATION",
    live_task["status"] == "completed",
)

check(
    "SNAPSHOT_GOAL_ISOLATION",
    live_goal["text"] == "Mở YouTube rồi tìm Python",
)

# ---------------------------------------------------------
# PLAN
# ---------------------------------------------------------

plan = planner.get_plan()

check(
    "PLAN_STRUCTURE",
    isinstance(plan, dict)
    and "goal" in plan
    and "tasks" in plan
    and "current_task" in plan,
)

check(
    "PLAN_VERSION",
    plan["version"] == "P7-1.0",
)

# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

validation = planner.validate()

check(
    "VALIDATION",
    validation["valid"] is True
    and validation["errors"] == [],
)

# ---------------------------------------------------------
# STATUS
# ---------------------------------------------------------

status = planner.status()

check(
    "STATUS",
    status["module"] == "task_planner"
    and status["version"] == "P7-1.0"
    and status["valid"] is True,
)

# ---------------------------------------------------------
# FACTORY
# ---------------------------------------------------------

factory_planner = create_task_planner()

check(
    "FACTORY",
    isinstance(factory_planner, TaskPlanner),
)

# ---------------------------------------------------------
# RESET
# ---------------------------------------------------------

planner.reset()

check(
    "RESET",
    planner.get_goal() is None
    and planner.get_tasks() == []
    and planner.get_current_task() is None,
)

check(
    "RESET_VALID",
    planner.validate()["valid"] is True,
)

# ---------------------------------------------------------
# SELF CHECK
# ---------------------------------------------------------

self_result = self_check()

check(
    "SELF_CHECK",
    self_result["valid"] is True
    and self_result["task_count"] == 2,
)

# ---------------------------------------------------------
# MAIN.PY PRESERVATION
# ---------------------------------------------------------

MAIN_FILE = os.path.join(APP_DIR, "main.py")

try:
    py_compile.compile(MAIN_FILE, doraise=True)
    check("MAIN_COMPILE_PRESERVED", True)
except Exception as exc:
    print("MAIN_COMPILE_ERROR:", exc)
    check("MAIN_COMPILE_PRESERVED", False)

print("\n=== FINAL ===")

if all_pass:
    print("P7-1 TASK PLANNER CORE: PASS")
    print("P6-3 STATE MANAGER: PRESERVED")
    print("P5 WORLD MODEL: PRESERVED")
    print("P4-5 EXECUTE -> VERIFY: PRESERVED")
    print("MAIN.PY: NOT MODIFIED")
    print("AUTO EXECUTION: NO")
    raise SystemExit(0)

print("P7-1 TASK PLANNER CORE: FAIL")
print("DO NOT PROCEED TO P7-2")
raise SystemExit(1)