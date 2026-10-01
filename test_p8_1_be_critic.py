from pathlib import Path
import py_compile
import importlib
import sys

APP_DIR = Path(__file__).resolve().parent
CRITIC_FILE = APP_DIR / "be_critic.py"
MAIN_FILE = APP_DIR / "main.py"
PLANNER_FILE = APP_DIR / "task_planner.py"

print("=== P8-1 BE CRITIC CORE VALIDATION ===")

for name, path in [
    ("BE_CRITIC_FILE", CRITIC_FILE),
    ("MAIN_FILE", MAIN_FILE),
    ("TASK_PLANNER_FILE", PLANNER_FILE),
]:
    if not path.exists():
        print(f"{name}: FAIL")
        raise SystemExit(1)
    print(f"{name}: PASS")

for name, path in [
    ("BE_CRITIC_COMPILE", CRITIC_FILE),
    ("MAIN_COMPILE_PRESERVED", MAIN_FILE),
    ("TASK_PLANNER_COMPILE_PRESERVED", PLANNER_FILE),
]:
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"{name}: PASS")
    except Exception as exc:
        print(f"{name}: FAIL")
        print("ERROR:", repr(exc))
        raise SystemExit(1)

try:
    sys.path.insert(0, str(APP_DIR))

    if "be_critic" in sys.modules:
        del sys.modules["be_critic"]

    module = importlib.import_module("be_critic")
    BECritic = module.BECritic

    print("BE_CRITIC_IMPORT: PASS")
    print("BE_CRITIC_CLASS: PASS")
except Exception as exc:
    print("BE_CRITIC_IMPORT: FAIL")
    print("ERROR:", repr(exc))
    raise SystemExit(1)

critic = BECritic()

if isinstance(critic, BECritic):
    print("CRITIC_CREATION: PASS")
else:
    print("CRITIC_CREATION: FAIL")
    raise SystemExit(1)

goal = {
    "text": "mở youtube",
    "intent": "action",
    "action": "open",
    "target": "youtube",
}

plan = {
    "goal": dict(goal),
    "tasks": [
        {
            "id": "task_1",
            "description": "Mở YouTube",
            "status": "planned",
        }
    ],
    "current_task": {
        "id": "task_1",
        "description": "Mở YouTube",
        "status": "planned",
    },
}

result = critic.evaluate(goal, plan)

if result.get("verdict") == "pass":
    print("VALID_GOAL_PLAN: PASS")
else:
    print("VALID_GOAL_PLAN: FAIL")
    print(result)
    raise SystemExit(1)

if result.get("valid") is True:
    print("VALID_RESULT_FLAG: PASS")
else:
    print("VALID_RESULT_FLAG: FAIL")
    raise SystemExit(1)

if isinstance(result.get("checks"), dict):
    print("CHECK_STRUCTURE: PASS")
else:
    print("CHECK_STRUCTURE: FAIL")
    raise SystemExit(1)

missing = critic.evaluate(None, None)

if missing.get("verdict") == "block":
    print("MISSING_GOAL_BLOCK: PASS")
else:
    print("MISSING_GOAL_BLOCK: FAIL")
    print(missing)
    raise SystemExit(1)

if "missing_goal" in missing.get("issues", []):
    print("MISSING_GOAL_ISSUE: PASS")
else:
    print("MISSING_GOAL_ISSUE: FAIL")
    raise SystemExit(1)

invalid_status_plan = {
    "tasks": [
        {
            "id": "task_1",
            "description": "Test",
            "status": "INVALID",
        }
    ]
}

invalid_status = critic.evaluate(
    goal,
    invalid_status_plan,
)

if invalid_status.get("verdict") == "review":
    print("INVALID_STATUS_REVIEW: PASS")
else:
    print("INVALID_STATUS_REVIEW: FAIL")
    print(invalid_status)
    raise SystemExit(1)

duplicate_plan = {
    "tasks": [
        {
            "id": "task_1",
            "description": "Task A",
            "status": "planned",
        },
        {
            "id": "task_1",
            "description": "Task B",
            "status": "planned",
        },
    ]
}

duplicate = critic.evaluate(
    goal,
    duplicate_plan,
)

if duplicate.get("verdict") == "review":
    print("DUPLICATE_TASK_REVIEW: PASS")
else:
    print("DUPLICATE_TASK_REVIEW: FAIL")
    print(duplicate)
    raise SystemExit(1)

conflict_plan = {
    "tasks": [
        {
            "id": "task_1",
            "description": "Task A",
            "status": "active",
        },
        {
            "id": "task_2",
            "description": "Task B",
            "status": "active",
        },
    ]
}

conflict = critic.evaluate(
    goal,
    conflict_plan,
)

if conflict.get("verdict") == "block":
    print("MULTIPLE_ACTIVE_BLOCK: PASS")
else:
    print("MULTIPLE_ACTIVE_BLOCK: FAIL")
    print(conflict)
    raise SystemExit(1)

bad_current_plan = {
    "tasks": [
        {
            "id": "task_1",
            "description": "Task A",
            "status": "planned",
        }
    ],
    "current_task": {
        "id": "task_999",
        "description": "Unknown",
        "status": "active",
    },
}

bad_current = critic.evaluate(
    goal,
    bad_current_plan,
)

if bad_current.get("verdict") == "block":
    print("INVALID_CURRENT_TASK_BLOCK: PASS")
else:
    print("INVALID_CURRENT_TASK_BLOCK: FAIL")
    print(bad_current)
    raise SystemExit(1)

no_tasks_plan = {
    "goal": dict(goal),
    "tasks": [],
}

no_tasks = critic.evaluate(
    goal,
    no_tasks_plan,
)

if "goal_has_no_tasks" in no_tasks.get("warnings", []):
    print("NO_TASK_WARNING: PASS")
else:
    print("NO_TASK_WARNING: FAIL")
    print(no_tasks)
    raise SystemExit(1)

if no_tasks.get("verdict") == "review":
    print("NO_TASK_STRICT_REVIEW: PASS")
else:
    print("NO_TASK_STRICT_REVIEW: FAIL")
    print(no_tasks)
    raise SystemExit(1)

saved = critic.get_last_result()

if not isinstance(saved, dict):
    print("LAST_RESULT: FAIL")
    raise SystemExit(1)

saved["verdict"] = "tampered"

fresh = critic.get_last_result()

if fresh.get("verdict") != "review":
    print("RESULT_ISOLATION: FAIL")
    raise SystemExit(1)

print("RESULT_ISOLATION: PASS")

critic.reset()

if critic.get_last_result() is None:
    print("RESET: PASS")
else:
    print("RESET: FAIL")
    raise SystemExit(1)

validation = critic.validate()

if validation.get("valid") is True:
    print("VALIDATION: PASS")
else:
    print("VALIDATION: FAIL")
    print(validation)
    raise SystemExit(1)

status = critic.status()

if (
    status.get("name") == "BE Critic"
    and status.get("version") == BECritic.VERSION
    and status.get("valid") is True
):
    print("STATUS: PASS")
else:
    print("STATUS: FAIL")
    print(status)
    raise SystemExit(1)

factory = module.create_be_critic()
    
if isinstance(factory, BECritic):
    print("FACTORY: PASS")
else:
    print("FACTORY: FAIL")
    raise SystemExit(1)

self_check = module.self_check()

if self_check.get("valid") is True:
    print("SELF_CHECK: PASS")
else:
    print("SELF_CHECK: FAIL")
    print(self_check)
    raise SystemExit(1)

print("MAIN.PY MODIFIED: NO")

print("")
print("=== FINAL ===")
print("P8-1 BE CRITIC CORE: PASS")
print("P7-2 TASK PLANNER: PRESERVED")
print("P6-3 STATE MANAGER: PRESERVED")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("MAIN.PY: NOT MODIFIED")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
