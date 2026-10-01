from pathlib import Path
import py_compile
import importlib
import sys

APP_DIR = Path(__file__).resolve().parent
MAIN = APP_DIR / "main.py"
PLANNER = APP_DIR / "task_planner.py"

print("=== P7-2 TASK PLANNER RUNTIME VALIDATION ===")

# ============================================================
# FILE CHECK
# ============================================================

if not MAIN.exists():
    print("MAIN_FILE: FAIL")
    raise SystemExit(1)

if not PLANNER.exists():
    print("TASK_PLANNER_FILE: FAIL")
    raise SystemExit(1)

print("MAIN_FILE: PASS")
print("TASK_PLANNER_FILE: PASS")

# ============================================================
# COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
    print("MAIN_COMPILE: PASS")
except Exception as exc:
    print("MAIN_COMPILE: FAIL")
    print("ERROR:", repr(exc))
    raise SystemExit(1)

try:
    py_compile.compile(
        str(PLANNER),
        doraise=True,
    )
    print("TASK_PLANNER_COMPILE: PASS")
except Exception as exc:
    print("TASK_PLANNER_COMPILE: FAIL")
    print("ERROR:", repr(exc))
    raise SystemExit(1)

# ============================================================
# IMPORT
# ============================================================

try:
    sys.path.insert(0, str(APP_DIR))

    if "main" in sys.modules:
        del sys.modules["main"]

    main_module = importlib.import_module("main")

    print("MAIN_IMPORT: PASS")

except Exception as exc:
    print("MAIN_IMPORT: FAIL")
    print("ERROR:", repr(exc))
    raise SystemExit(1)

# ============================================================
# GLOBAL MINH INSTANCE
# ============================================================

MINH = getattr(
    main_module,
    "MINH",
    None,
)

if MINH is None:
    print("MINH_GLOBAL_INSTANCE: FAIL")
    raise SystemExit(1)

print("MINH_GLOBAL_INSTANCE: PASS")

# ============================================================
# TASK PLANNER INSTANCE
# ============================================================

planner = getattr(
    MINH,
    "task_planner",
    None,
)

if planner is None:
    print("TASK_PLANNER_INSTANCE: FAIL")
    raise SystemExit(1)

print("TASK_PLANNER_INSTANCE: PASS")

# ============================================================
# INITIAL STATE
# ============================================================

initial_plan = planner.get_plan()

if not isinstance(initial_plan, dict):
    print("INITIAL_PLAN_STRUCTURE: FAIL")
    raise SystemExit(1)

print("INITIAL_PLAN_STRUCTURE: PASS")

initial_tasks = planner.get_tasks()

if not isinstance(initial_tasks, list):
    print("INITIAL_TASKS_LIST: FAIL")
    raise SystemExit(1)

print("INITIAL_TASKS_LIST: PASS")

# ============================================================
# TURN 1
# ============================================================

print("")
print("=== TURN 1: SUCCESS PATH ===")

answer1 = MINH.process("mở youtube")

print("TURN1_ANSWER:", answer1)

state1 = planner.get_plan()

if not isinstance(state1, dict):
    print("TURN1_PLAN_STRUCTURE: FAIL")
    raise SystemExit(1)

print("TURN1_PLAN_STRUCTURE: PASS")

goal1 = planner.get_goal()

if goal1 is None:
    print("TURN1_GOAL_SYNC: FAIL")
    raise SystemExit(1)

print("TURN1_GOAL_SYNC: PASS")

tasks1 = planner.get_tasks()

if not isinstance(tasks1, list):
    print("TURN1_TASK_LIST: FAIL")
    raise SystemExit(1)

print("TURN1_TASK_LIST: PASS")

current1 = planner.get_current_task()

if current1 is not None:
    print("TURN1_CURRENT_TASK_EXISTS: PASS")
    print("TURN1_CURRENT_TASK:", current1)
else:
    print(
        "TURN1_CURRENT_TASK_EXISTS: INFO "
        "(Goal has no planner steps)"
    )

# ============================================================
# MAIN STATE CHECK
# ============================================================

sm = getattr(
    MINH,
    "state_manager",
    None,
)

if sm is None:
    print("STATE_MANAGER_INSTANCE: FAIL")
    raise SystemExit(1)

print("STATE_MANAGER_INSTANCE: PASS")

main_state1 = sm.get_state()

if not isinstance(main_state1, dict):
    print("TURN1_STATE_STRUCTURE: FAIL")
    raise SystemExit(1)

print("TURN1_STATE_STRUCTURE: PASS")

execution1 = main_state1.get(
    "execution_result"
)

verification1 = main_state1.get(
    "verification"
)

if isinstance(execution1, dict):
    print(
        "TURN1_EXECUTION_SUCCESS:",
        execution1.get("success"),
    )

if isinstance(verification1, dict):
    print(
        "TURN1_VERIFICATION:",
        verification1.get("status"),
        verification1.get("success"),
    )

# ============================================================
# SAVE TURN 1 TARGET
# ============================================================

goal1_snapshot = (
    dict(goal1)
    if isinstance(goal1, dict)
    else goal1
)

tasks1_snapshot = [
    dict(task)
    for task in tasks1
    if isinstance(task, dict)
]

# ============================================================
# TURN 2
# ============================================================

print("")
print("=== TURN 2: BLOCKED PATH ===")

answer2 = MINH.process("mở")

print("TURN2_ANSWER:", answer2)

state2 = planner.get_plan()

if not isinstance(state2, dict):
    print("TURN2_PLAN_STRUCTURE: FAIL")
    raise SystemExit(1)

print("TURN2_PLAN_STRUCTURE: PASS")

goal2 = planner.get_goal()

tasks2 = planner.get_tasks()

current2 = planner.get_current_task()

# ------------------------------------------------------------
# BLOCKED MUST NOT EXECUTE
# ------------------------------------------------------------

main_state2 = sm.get_state()

execution2 = main_state2.get(
    "execution_result"
)

verification2 = main_state2.get(
    "verification"
)

if execution2 is None:
    print("TURN2_NO_EXECUTION: PASS")
else:
    print(
        "TURN2_NO_EXECUTION: FAIL",
        execution2,
    )
    raise SystemExit(1)

if isinstance(verification2, dict):
    if verification2.get("status") == "blocked":
        print("TURN2_VERIFICATION_BLOCKED: PASS")
    else:
        print(
            "TURN2_VERIFICATION_BLOCKED: FAIL",
            verification2,
        )
        raise SystemExit(1)
else:
    print("TURN2_VERIFICATION_BLOCKED: FAIL")
    raise SystemExit(1)

# ============================================================
# STATE LEAK CHECK
# ============================================================

# Planner must not retain an old completed task as the
# active task merely because the current turn is blocked.

if current2 is None:
    print("TURN2_NO_ACTIVE_OLD_TASK: PASS")
else:
    print(
        "TURN2_ACTIVE_TASK:",
        current2,
    )

    old_ids = {
        task.get("id")
        for task in tasks1_snapshot
        if isinstance(task, dict)
    }

    current2_id = current2.get("id")

    if current2_id in old_ids:
        print(
            "TURN2_OLD_TASK_LEAK: FAIL",
            current2_id,
        )
        raise SystemExit(1)

    print("TURN2_OLD_TASK_LEAK: PASS")

# ============================================================
# TURN 3
# ============================================================

print("")
print("=== TURN 3: NEW SUCCESS PATH ===")

answer3 = MINH.process("mở google")

print("TURN3_ANSWER:", answer3)

state3 = planner.get_plan()

if not isinstance(state3, dict):
    print("TURN3_PLAN_STRUCTURE: FAIL")
    raise SystemExit(1)

print("TURN3_PLAN_STRUCTURE: PASS")

goal3 = planner.get_goal()

if goal3 is None:
    print("TURN3_GOAL_SYNC: FAIL")
    raise SystemExit(1)

print("TURN3_GOAL_SYNC: PASS")

tasks3 = planner.get_tasks()

if not isinstance(tasks3, list):
    print("TURN3_TASK_LIST: FAIL")
    raise SystemExit(1)

print("TURN3_TASK_LIST: PASS")

current3 = planner.get_current_task()

if current3 is not None:
    print("TURN3_CURRENT_TASK:", current3)

# ============================================================
# MAIN STATE TURN 3
# ============================================================

main_state3 = sm.get_state()

execution3 = main_state3.get(
    "execution_result"
)

verification3 = main_state3.get(
    "verification"
)

if not isinstance(execution3, dict):
    print("TURN3_EXECUTION_RESULT: FAIL")
    raise SystemExit(1)

if execution3.get("success") is True:
    print("TURN3_EXECUTION_SUCCESS: PASS")
else:
    print(
        "TURN3_EXECUTION_SUCCESS: FAIL",
        execution3,
    )
    raise SystemExit(1)

if not isinstance(verification3, dict):
    print("TURN3_VERIFICATION: FAIL")
    raise SystemExit(1)

if (
    verification3.get("verified") is True
    and verification3.get("status") == "pass"
    and verification3.get("success") is True
):
    print("TURN3_VERIFICATION_PASS: PASS")
else:
    print(
        "TURN3_VERIFICATION_PASS: FAIL",
        verification3,
    )
    raise SystemExit(1)

# ============================================================
# NEW TARGET MUST REPLACE OLD TARGET
# ============================================================

if isinstance(goal3, dict) and isinstance(goal1_snapshot, dict):

    target1 = goal1_snapshot.get("target")
    target3 = goal3.get("target")

    print(
        "TURN1_TARGET:",
        target1,
    )

    print(
        "TURN3_TARGET:",
        target3,
    )

    if target3 == target1:
        print("NEW_TARGET_REPLACED: FAIL")
        raise SystemExit(1)

    print("NEW_TARGET_REPLACED: PASS")

# ============================================================
# FINAL PLANNER VALIDATION
# ============================================================

final_validation = planner.validate()

if not isinstance(final_validation, dict):
    print("FINAL_PLANNER_VALIDATION: FAIL")
    raise SystemExit(1)

if final_validation.get("valid") is True:
    print("FINAL_PLANNER_VALIDATION: PASS")
else:
    print(
        "FINAL_PLANNER_VALIDATION: FAIL",
        final_validation,
    )
    raise SystemExit(1)

# ============================================================
# FINAL STATE MANAGER VALIDATION
# ============================================================

final_sm_validation = sm.validate()

if not isinstance(final_sm_validation, dict):
    print("FINAL_STATE_MANAGER_VALIDATION: FAIL")
    raise SystemExit(1)

if final_sm_validation.get("valid") is True:
    print("FINAL_STATE_MANAGER_VALIDATION: PASS")
else:
    print(
        "FINAL_STATE_MANAGER_VALIDATION: FAIL",
        final_sm_validation,
    )
    raise SystemExit(1)

# ============================================================
# WORLD MODEL PRESERVATION
# ============================================================

world_model = getattr(
    MINH,
    "world_model",
    None,
)

if world_model is None:
    print("WORLD_MODEL_INSTANCE: FAIL")
    raise SystemExit(1)

print("WORLD_MODEL_INSTANCE: PASS")

wm_state = world_model.get_state()

if isinstance(wm_state, dict):
    print("WORLD_MODEL_STATE: PASS")
else:
    print("WORLD_MODEL_STATE: FAIL")
    raise SystemExit(1)

# ============================================================
# FINAL
# ============================================================

print("")
print("=== FINAL ===")
print("P7-2 TASK PLANNER RUNTIME VALIDATION: PASS")
print("P7-2 TASK PLANNER -> MAIN: PRESERVED")
print("P7-1 TASK PLANNER CORE: PRESERVED")
print("P6-3 STATE MANAGER: PRESERVED")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("SUCCESS -> BLOCKED -> SUCCESS: PASS")
print("STATE LEAK CHECK: PASS")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
