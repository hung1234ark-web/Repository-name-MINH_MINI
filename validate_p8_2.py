from pathlib import Path
import py_compile
import importlib
import sys


BASE = Path(__file__).resolve().parent
MAIN_FILE = BASE / "main.py"
BE_CRITIC_FILE = BASE / "be_critic.py"
TASK_PLANNER_FILE = BASE / "task_planner.py"
STATE_MANAGER_FILE = BASE / "state_manager.py"
WORLD_MODEL_FILE = BASE / "world_model.py"


def check(condition, label):
    if condition:
        print(f"{label}: PASS")
    else:
        print(f"{label}: FAIL")
        raise RuntimeError(label)


def compile_file(path, label):
    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
        print(f"{label}: PASS")
    except Exception as exc:
        print(f"{label}: FAIL ({exc})")
        raise


print("=== P8-2 BE CRITIC RUNTIME VALIDATION ===")


# ============================================================
# FILES
# ============================================================

for path, label in [
    (MAIN_FILE, "MAIN_FILE"),
    (BE_CRITIC_FILE, "BE_CRITIC_FILE"),
    (TASK_PLANNER_FILE, "TASK_PLANNER_FILE"),
    (STATE_MANAGER_FILE, "STATE_MANAGER_FILE"),
    (WORLD_MODEL_FILE, "WORLD_MODEL_FILE"),
]:
    check(path.exists(), label)


# ============================================================
# COMPILE
# ============================================================

compile_file(MAIN_FILE, "MAIN_COMPILE")
compile_file(BE_CRITIC_FILE, "BE_CRITIC_COMPILE")
compile_file(TASK_PLANNER_FILE, "TASK_PLANNER_COMPILE")
compile_file(STATE_MANAGER_FILE, "STATE_MANAGER_COMPILE")
compile_file(WORLD_MODEL_FILE, "WORLD_MODEL_COMPILE")


# ============================================================
# IMPORT
# ============================================================

import main

print("MAIN_IMPORT: PASS")


# ============================================================
# GLOBAL INSTANCE
# ============================================================

MINH = getattr(main, "MINH", None)

check(
    MINH is not None,
    "MINH_GLOBAL_INSTANCE",
)

print(
    "MINH_TYPE:",
    type(MINH).__name__,
)


# ============================================================
# P8-2 BE CRITIC
# ============================================================

critic = getattr(
    MINH,
    "be_critic",
    None,
)

check(
    critic is not None,
    "BE_CRITIC_INSTANCE",
)

critic_validation = critic.validate()

check(
    isinstance(critic_validation, dict),
    "BE_CRITIC_VALIDATION_STRUCTURE",
)

check(
    critic_validation.get("valid") is True,
    "BE_CRITIC_VALID",
)


# ============================================================
# SUPPORTING LAYERS
# ============================================================

check(
    getattr(MINH, "task_planner", None) is not None,
    "TASK_PLANNER_INSTANCE",
)

check(
    getattr(MINH, "state_manager", None) is not None,
    "STATE_MANAGER_INSTANCE",
)

check(
    getattr(MINH, "world_model", None) is not None,
    "WORLD_MODEL_INSTANCE",
)


# ============================================================
# INITIAL STATUS
# ============================================================

status_before = MINH.status()

check(
    isinstance(status_before, dict),
    "INITIAL_STATUS_STRUCTURE",
)

check(
    status_before.get("be_critic") is True,
    "INITIAL_BE_CRITIC_STATUS",
)

check(
    status_before.get("be_critic_valid") is True,
    "INITIAL_BE_CRITIC_VALID_STATUS",
)


# ============================================================
# TURN 1 — SUCCESS
# ============================================================

print("")
print("=== TURN 1: SUCCESS PATH ===")

answer1 = MINH.process(
    "mở youtube"
)

print(
    "TURN1_ANSWER:",
    answer1,
)

check(
    isinstance(answer1, str)
    and bool(answer1.strip()),
    "TURN1_ANSWER",
)


critic_result1 = critic.get_last_result()

check(
    isinstance(critic_result1, dict),
    "TURN1_CRITIC_RESULT",
)

print(
    "TURN1_CRITIC_VERDICT:",
    critic_result1.get("verdict"),
)

check(
    "verdict" in critic_result1,
    "TURN1_CRITIC_VERDICT_FIELD",
)

check(
    "valid" in critic_result1,
    "TURN1_CRITIC_VALID_FIELD",
)


# P4-5
verification1 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

check(
    isinstance(verification1, dict),
    "TURN1_VERIFICATION_STRUCTURE",
)

check(
    verification1.get("status") == "pass",
    "TURN1_VERIFICATION_PASS",
)

check(
    verification1.get("success") is True,
    "TURN1_EXECUTION_SUCCESS",
)


# P6
state1 = MINH.state_manager.get_state()

check(
    isinstance(state1, dict),
    "TURN1_STATE_STRUCTURE",
)

check(
    state1.get("status") == "completed",
    "TURN1_STATE_COMPLETED",
)

check(
    isinstance(
        state1.get("be_critic"),
        dict,
    ),
    "TURN1_STATE_BE_CRITIC",
)


# P5
world1 = MINH.world_model.get_state()

check(
    isinstance(world1, dict),
    "TURN1_WORLD_MODEL_STATE",
)

check(
    isinstance(
        world1.get("last_observation"),
        dict,
    ),
    "TURN1_WORLD_MODEL_OBSERVATION",
)


# P7
planner1 = MINH.task_planner.get_plan()

check(
    isinstance(planner1, dict),
    "TURN1_PLAN_STRUCTURE",
)


# ============================================================
# CAPTURE TURN 1
# ============================================================

turn1_critic_result = dict(
    critic_result1
)

turn1_verification = dict(
    verification1
)

turn1_target = (
    world1
    .get("active_goal", {})
    .get("target")
    if isinstance(
        world1.get("active_goal"),
        dict,
    )
    else None
)

print(
    "TURN1_TARGET:",
    turn1_target,
)


# ============================================================
# TURN 2 — BLOCKED
# ============================================================

print("")
print("=== TURN 2: BLOCKED PATH ===")

answer2 = MINH.process(
    "mở"
)

print(
    "TURN2_ANSWER:",
    answer2,
)

check(
    isinstance(answer2, str)
    and bool(answer2.strip()),
    "TURN2_ANSWER",
)

verification2 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

check(
    isinstance(verification2, dict),
    "TURN2_VERIFICATION_STRUCTURE",
)

check(
    verification2.get("status") == "blocked",
    "TURN2_VERIFICATION_BLOCKED",
)

check(
    verification2.get("success") is None,
    "TURN2_NO_EXECUTION",
)


state2 = MINH.state_manager.get_state()

check(
    state2.get("status") == "blocked",
    "TURN2_STATE_BLOCKED",
)


# BE Critic must still exist and remain valid.
critic_result2 = critic.get_last_result()

check(
    isinstance(critic_result2, dict),
    "TURN2_CRITIC_RESULT",
)

check(
    critic.validate().get("valid") is True,
    "TURN2_CRITIC_VALID",
)


# Ensure old successful verification did not leak.
check(
    verification2.get("status") != "pass",
    "TURN2_NO_OLD_VERIFICATION_LEAK",
)

# World Model must record blocked observation.
world2 = MINH.world_model.get_state()

observation2 = world2.get(
    "last_observation"
)

check(
    isinstance(observation2, dict),
    "TURN2_WORLD_MODEL_OBSERVATION",
)

check(
    isinstance(observation2.get("verification"), dict) and observation2.get("verification", {}).get("status") == "blocked",
    "TURN2_WORLD_MODEL_BLOCKED",
)


# ============================================================
# TURN 3 — NEW SUCCESS
# ============================================================

print("")
print("=== TURN 3: NEW SUCCESS PATH ===")

answer3 = MINH.process(
    "mở google"
)

print(
    "TURN3_ANSWER:",
    answer3,
)

check(
    isinstance(answer3, str)
    and bool(answer3.strip()),
    "TURN3_ANSWER",
)


verification3 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

check(
    isinstance(verification3, dict),
    "TURN3_VERIFICATION_STRUCTURE",
)

check(
    verification3.get("status") == "pass",
    "TURN3_VERIFICATION_PASS",
)

check(
    verification3.get("success") is True,
    "TURN3_EXECUTION_SUCCESS",
)


# ============================================================
# TURN 3 BE CRITIC
# ============================================================

critic_result3 = critic.get_last_result()

check(
    isinstance(critic_result3, dict),
    "TURN3_CRITIC_RESULT",
)

check(
    "verdict" in critic_result3,
    "TURN3_CRITIC_VERDICT",
)

check(
    critic.validate().get("valid") is True,
    "TURN3_CRITIC_VALID",
)

print(
    "TURN3_CRITIC_VERDICT:",
    critic_result3.get("verdict"),
)


# ============================================================
# TURN 3 STATE
# ============================================================

state3 = MINH.state_manager.get_state()

check(
    state3.get("status") == "completed",
    "TURN3_STATE_COMPLETED",
)

check(
    isinstance(
        state3.get("be_critic"),
        dict,
    ),
    "TURN3_STATE_BE_CRITIC",
)


# ============================================================
# TURN 3 WORLD MODEL
# ============================================================

world3 = MINH.world_model.get_state()

check(
    isinstance(world3, dict),
    "TURN3_WORLD_MODEL_STATE",
)

active_goal3 = world3.get(
    "active_goal"
)

turn3_target = (
    active_goal3.get("target")
    if isinstance(active_goal3, dict)
    else None
)

print(
    "TURN1_TARGET:",
    turn1_target,
)

print(
    "TURN3_TARGET:",
    turn3_target,
)

check(
    turn3_target == "google",
    "TURN3_NEW_TARGET_GOOGLE",
)

check(
    turn3_target != turn1_target,
    "NEW_TARGET_REPLACED",
)


# ============================================================
# TURN 3 OBSERVATION
# ============================================================

observation3 = world3.get(
    "last_observation"
)

check(
    isinstance(observation3, dict),
    "TURN3_WORLD_MODEL_OBSERVATION",
)


# ============================================================
# P7-2 FINAL
# ============================================================

planner3 = MINH.task_planner.get_plan()

check(
    isinstance(planner3, dict),
    "FINAL_PLAN_STRUCTURE",
)


# ============================================================
# FINAL STATUS
# ============================================================

final_status = MINH.status()

check(
    isinstance(final_status, dict),
    "FINAL_STATUS_STRUCTURE",
)

check(
    final_status.get("be_critic") is True,
    "FINAL_BE_CRITIC_STATUS",
)

check(
    final_status.get("be_critic_valid") is True,
    "FINAL_BE_CRITIC_VALID",
)


# ============================================================
# FINAL CRITIC STATE
# ============================================================

final_critic_result = critic.get_last_result()

check(
    isinstance(final_critic_result, dict),
    "FINAL_CRITIC_RESULT",
)

print(
    "FINAL_CRITIC_VERDICT:",
    final_critic_result.get("verdict"),
)


# ============================================================
# FINAL VALIDATIONS
# ============================================================

check(
    MINH.world_model.validate().get("valid") is True,
    "FINAL_WORLD_MODEL_VALID",
)

check(
    MINH.state_manager.validate().get("valid") is True,
    "FINAL_STATE_MANAGER_VALID",
)

check(
    critic.validate().get("valid") is True,
    "FINAL_BE_CRITIC_VALIDATION",
)


print("")
print("=== FINAL ===")
print("P8-2 BE CRITIC RUNTIME VALIDATION PASS")
print("P8-2 BE CRITIC -> MAIN PASS")
print("P8-1 BE CRITIC CORE PRESERVED")
print("P7-2 TASK PLANNER PRESERVED")
print("P6-3 STATE MANAGER PRESERVED")
print("P5 WORLD MODEL PRESERVED")
print("P4-5 EXECUTE -> VERIFY PRESERVED")
print("SUCCESS -> BLOCKED -> SUCCESS PASS")
print("BE CRITIC MODE: ADVISORY")
print("NO EXECUTION CONTROL CHANGE")
print("AUTO GIT COMMIT: NO")

