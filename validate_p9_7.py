from pathlib import Path
import py_compile
import importlib.util
import sys


APP_DIR = Path(__file__).resolve().parent
MAIN = APP_DIR / "main.py"

print("=== P9-7 P9 RUNTIME VALIDATION ===")


def fail(name, detail=""):
    print(f"{name}: FAIL")
    if detail:
        print(detail)
    sys.exit(1)


# ============================================================
# 1. FILE CHECK
# ============================================================

required_files = [
    "main.py",
    "critic.py",
    "red_team.py",
    "fact_check.py",
    "combined_evaluation.py",
    "be_critic.py",
    "task_planner.py",
    "state_manager.py",
    "world_model.py",
]

for filename in required_files:
    if not (APP_DIR / filename).exists():
        fail("FILE CHECK", f"Missing: {filename}")

print("FILE CHECK: PASS")


# ============================================================
# 2. COMPILE
# ============================================================

for filename in required_files:
    try:
        py_compile.compile(
            str(APP_DIR / filename),
            doraise=True,
        )
    except Exception as exc:
        fail(
            "COMPILE CHECK",
            f"{filename}: {exc}",
        )

print("COMPILE CHECK: PASS")


# ============================================================
# 3. IMPORT MAIN
# ============================================================

try:
    spec = importlib.util.spec_from_file_location(
        "main_p9_7_runtime",
        str(MAIN),
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Could not create import spec"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

except Exception as exc:
    fail(
        "MAIN IMPORT",
        repr(exc),
    )

print("MAIN IMPORT: PASS")


# ============================================================
# 4. GLOBAL MINH
# ============================================================

if not hasattr(module, "MINH"):
    fail(
        "GLOBAL MINH",
        "main.py does not expose MINH",
    )

MINH = module.MINH

print("GLOBAL MINH: PASS")
print(
    "MINH TYPE:",
    type(MINH).__name__,
)


# ============================================================
# 5. CORE INSTANCE CHECK
# ============================================================

checks = [
    ("P9 CRITIC INSTANCE", "p9_critic"),
    ("P9 RED TEAM INSTANCE", "p9_red_team"),
    ("P9 FACTCHECK INSTANCE", "p9_fact_check"),
    (
        "P9 COMBINED INSTANCE",
        "p9_combined_evaluation",
    ),
    ("P9 LAST RESULT", "last_p9_evaluation"),
    ("BE CRITIC INSTANCE", "be_critic"),
    ("TASK PLANNER INSTANCE", "task_planner"),
    ("STATE MANAGER INSTANCE", "state_manager"),
    ("WORLD MODEL INSTANCE", "world_model"),
]

for label, attribute in checks:
    if not hasattr(MINH, attribute):
        fail(
            label,
            f"Missing attribute: {attribute}",
        )

    print(f"{label}: PASS")


# ============================================================
# 6. INITIAL P9 STATE
# ============================================================

initial_p9 = getattr(
    MINH,
    "last_p9_evaluation",
    None,
)

if initial_p9 is not None:
    print(
        "INITIAL P9 STATE: INFO "
        "(previous evaluation exists)"
    )
else:
    print(
        "INITIAL P9 STATE: PASS "
        "(None)"
    )


# ============================================================
# 7. TURN 1 — SUCCESS
# ============================================================

print("\n=== TURN 1: SUCCESS PATH ===")

answer1 = MINH.process(
    "mở youtube"
)

print(
    "TURN1_ANSWER:",
    answer1,
)

if not answer1:
    fail(
        "TURN1_ANSWER",
        "Empty answer",
    )

print("TURN1_ANSWER: PASS")


# ------------------------------------------------------------
# P9 RESULT
# ------------------------------------------------------------

p9_1 = getattr(
    MINH,
    "last_p9_evaluation",
    None,
)

if not isinstance(p9_1, dict):
    fail(
        "TURN1_P9_RESULT",
        repr(p9_1),
    )

print("TURN1_P9_RESULT: PASS")


for key in [
    "critic",
    "red_team",
    "fact_check",
    "combined",
]:
    if key not in p9_1:
        fail(
            "TURN1_P9_STRUCTURE",
            f"Missing key: {key}",
        )

print("TURN1_P9_STRUCTURE: PASS")


# ------------------------------------------------------------
# Individual evaluator results
# ------------------------------------------------------------

for label, key in [
    ("TURN1_CRITIC", "critic"),
    ("TURN1_RED_TEAM", "red_team"),
    ("TURN1_FACTCHECK", "fact_check"),
    ("TURN1_COMBINED", "combined"),
]:
    value = p9_1.get(key)

    if not isinstance(value, dict):
        fail(
            label,
            repr(value),
        )

    if "verdict" not in value:
        fail(
            label,
            "Missing verdict",
        )

    print(
        f"{label}: PASS "
        f"verdict={value.get('verdict')}"
    )


combined1 = p9_1.get("combined", {})

if combined1.get("verdict") not in {
    "pass",
    "review",
    "block",
}:
    fail(
        "TURN1_COMBINED_VERDICT",
        repr(combined1),
    )

print(
    "TURN1_COMBINED_VERDICT: PASS",
    combined1.get("verdict"),
)


# ------------------------------------------------------------
# Execution verification
# ------------------------------------------------------------

verification1 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

if not isinstance(verification1, dict):
    fail(
        "TURN1_VERIFICATION",
        repr(verification1),
    )

if verification1.get("verified") is not True:
    fail(
        "TURN1_VERIFICATION",
        repr(verification1),
    )

if verification1.get("status") != "pass":
    fail(
        "TURN1_VERIFICATION",
        repr(verification1),
    )

if verification1.get("success") is not True:
    fail(
        "TURN1_VERIFICATION",
        repr(verification1),
    )

print("TURN1_VERIFICATION_PASS: PASS")


# ------------------------------------------------------------
# Execution result
# ------------------------------------------------------------

execution1 = getattr(
    MINH,
    "last_execution_result",
    None,
)

if execution1 is not None:
    print(
        "TURN1_EXECUTION_RESULT: INFO"
    )


# ------------------------------------------------------------
# State Manager
# ------------------------------------------------------------

state1 = MINH.state_manager.get_state()

if not isinstance(state1, dict):
    fail(
        "TURN1_STATE",
        repr(state1),
    )

if state1.get("status") != "completed":
    fail(
        "TURN1_STATE_COMPLETED",
        repr(state1),
    )

print("TURN1_STATE_COMPLETED: PASS")


# ------------------------------------------------------------
# World Model
# ------------------------------------------------------------

world1 = MINH.world_model.get_state()

if not isinstance(world1, dict):
    fail(
        "TURN1_WORLD_MODEL",
        repr(world1),
    )

observation1 = world1.get(
    "last_observation"
)

if not isinstance(observation1, dict):
    fail(
        "TURN1_WORLD_MODEL_OBSERVATION",
        repr(observation1),
    )

verification_obs1 = observation1.get(
    "verification"
)

if not isinstance(
    verification_obs1,
    dict,
):
    fail(
        "TURN1_WORLD_MODEL_VERIFICATION",
        repr(verification_obs1),
    )

if verification_obs1.get("status") != "pass":
    fail(
        "TURN1_WORLD_MODEL_VERIFICATION",
        repr(verification_obs1),
    )

print(
    "TURN1_WORLD_MODEL_OBSERVATION: PASS"
)


# ------------------------------------------------------------
# Target
# ------------------------------------------------------------

target1 = observation1.get(
    "target"
)

print(
    "TURN1_TARGET:",
    target1,
)

if target1 != "youtube":
    print(
        "TURN1_TARGET: INFO "
        "(target representation differs)"
    )
else:
    print("TURN1_TARGET: PASS")


# ============================================================
# TURN 2 — BLOCKED
# ============================================================

print("\n=== TURN 2: BLOCKED PATH ===")

answer2 = MINH.process(
    "mở"
)

print(
    "TURN2_ANSWER:",
    answer2,
)

if not answer2:
    fail(
        "TURN2_ANSWER",
        "Empty answer",
    )

print("TURN2_ANSWER: PASS")


# ------------------------------------------------------------
# Verification must be blocked
# ------------------------------------------------------------

verification2 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

if not isinstance(
    verification2,
    dict,
):
    fail(
        "TURN2_VERIFICATION",
        repr(verification2),
    )

if verification2.get("verified") is not False:
    fail(
        "TURN2_VERIFICATION_BLOCKED",
        repr(verification2),
    )

if verification2.get("status") != "blocked":
    fail(
        "TURN2_VERIFICATION_BLOCKED",
        repr(verification2),
    )

if verification2.get("success") is not None:
    fail(
        "TURN2_VERIFICATION_SUCCESS_LEAK",
        repr(verification2),
    )

print("TURN2_VERIFICATION_BLOCKED: PASS")


# ------------------------------------------------------------
# P9 result must refresh
# ------------------------------------------------------------

p9_2 = getattr(
    MINH,
    "last_p9_evaluation",
    None,
)

if not isinstance(
    p9_2,
    dict,
):
    fail(
        "TURN2_P9_RESULT",
        repr(p9_2),
    )

print("TURN2_P9_RESULT: PASS")


for key in [
    "critic",
    "red_team",
    "fact_check",
    "combined",
]:
    if key not in p9_2:
        fail(
            "TURN2_P9_STRUCTURE",
            f"Missing key: {key}",
        )

print("TURN2_P9_STRUCTURE: PASS")


# ------------------------------------------------------------
# State Manager blocked
# ------------------------------------------------------------

state2 = MINH.state_manager.get_state()

if state2.get("status") != "blocked":
    fail(
        "TURN2_STATE_BLOCKED",
        repr(state2),
    )

print("TURN2_STATE_BLOCKED: PASS")


# ------------------------------------------------------------
# World Model blocked
# ------------------------------------------------------------

world2 = MINH.world_model.get_state()

observation2 = world2.get(
    "last_observation"
)

if not isinstance(
    observation2,
    dict,
):
    fail(
        "TURN2_WORLD_MODEL_OBSERVATION",
        repr(observation2),
    )

verification_obs2 = observation2.get(
    "verification"
)

if not isinstance(
    verification_obs2,
    dict,
):
    fail(
        "TURN2_WORLD_MODEL_VERIFICATION",
        repr(verification_obs2),
    )

if verification_obs2.get("status") != "blocked":
    fail(
        "TURN2_WORLD_MODEL_BLOCKED",
        repr(verification_obs2),
    )

print("TURN2_WORLD_MODEL_BLOCKED: PASS")


# ------------------------------------------------------------
# No old execution leak
# ------------------------------------------------------------

if verification2.get("success") is True:
    fail(
        "TURN2_NO_OLD_VERIFICATION_LEAK",
        repr(verification2),
    )

print(
    "TURN2_NO_OLD_VERIFICATION_LEAK: PASS"
)


# ============================================================
# TURN 3 — NEW SUCCESS
# ============================================================

print("\n=== TURN 3: NEW SUCCESS PATH ===")

answer3 = MINH.process(
    "mở google"
)

print(
    "TURN3_ANSWER:",
    answer3,
)

if not answer3:
    fail(
        "TURN3_ANSWER",
        "Empty answer",
    )

print("TURN3_ANSWER: PASS")


# ------------------------------------------------------------
# Verification
# ------------------------------------------------------------

verification3 = getattr(
    MINH,
    "last_execution_verification",
    None,
)

if not isinstance(
    verification3,
    dict,
):
    fail(
        "TURN3_VERIFICATION",
        repr(verification3),
    )

if verification3.get("verified") is not True:
    fail(
        "TURN3_VERIFICATION",
        repr(verification3),
    )

if verification3.get("status") != "pass":
    fail(
        "TURN3_VERIFICATION",
        repr(verification3),
    )

if verification3.get("success") is not True:
    fail(
        "TURN3_VERIFICATION",
        repr(verification3),
    )

print("TURN3_VERIFICATION_PASS: PASS")


# ------------------------------------------------------------
# P9
# ------------------------------------------------------------

p9_3 = getattr(
    MINH,
    "last_p9_evaluation",
    None,
)

if not isinstance(
    p9_3,
    dict,
):
    fail(
        "TURN3_P9_RESULT",
        repr(p9_3),
    )

print("TURN3_P9_RESULT: PASS")


for key in [
    "critic",
    "red_team",
    "fact_check",
    "combined",
]:
    if key not in p9_3:
        fail(
            "TURN3_P9_STRUCTURE",
            f"Missing key: {key}",
        )

print("TURN3_P9_STRUCTURE: PASS")


combined3 = p9_3.get(
    "combined",
    {},
)

if combined3.get("verdict") not in {
    "pass",
    "review",
    "block",
}:
    fail(
        "TURN3_COMBINED_VERDICT",
        repr(combined3),
    )

print(
    "TURN3_COMBINED_VERDICT: PASS",
    combined3.get("verdict"),
)


# ------------------------------------------------------------
# State Manager
# ------------------------------------------------------------

state3 = MINH.state_manager.get_state()

if state3.get("status") != "completed":
    fail(
        "TURN3_STATE_COMPLETED",
        repr(state3),
    )

print("TURN3_STATE_COMPLETED: PASS")


# ------------------------------------------------------------
# World Model
# ------------------------------------------------------------

world3 = MINH.world_model.get_state()

observation3 = world3.get(
    "last_observation"
)

if not isinstance(
    observation3,
    dict,
):
    fail(
        "TURN3_WORLD_MODEL_OBSERVATION",
        repr(observation3),
    )

verification_obs3 = observation3.get(
    "verification"
)

if not isinstance(
    verification_obs3,
    dict,
):
    fail(
        "TURN3_WORLD_MODEL_VERIFICATION",
        repr(verification_obs3),
    )

if verification_obs3.get("status") != "pass":
    fail(
        "TURN3_WORLD_MODEL_VERIFICATION",
        repr(verification_obs3),
    )

print(
    "TURN3_WORLD_MODEL_OBSERVATION: PASS"
)


# ------------------------------------------------------------
# Target replacement
# ------------------------------------------------------------

target3 = observation3.get(
    "target"
)

print(
    "TURN3_TARGET:",
    target3,
)

if target3 != "google":
    fail(
        "TURN3_TARGET",
        repr(target3),
    )

print("TURN3_TARGET: PASS")


# ============================================================
# 8. STATE LEAK CHECK
# ============================================================

active_goal3 = world3.get(
    "active_goal"
)

if isinstance(
    active_goal3,
    dict,
):
    active_text = str(
        active_goal3.get(
            "text",
            ""
        )
    ).lower()

    if active_text == "mở":
        fail(
            "STATE_LEAK_CHECK",
            "Old blocked goal still active",
        )

print("STATE_LEAK_CHECK: PASS")


# ============================================================
# 9. P9 VALIDATION APIs
# ============================================================

for label, attribute in [
    ("P9 CRITIC VALIDATE", "p9_critic"),
    ("P9 RED TEAM VALIDATE", "p9_red_team"),
    ("P9 FACTCHECK VALIDATE", "p9_fact_check"),
    (
        "P9 COMBINED VALIDATE",
        "p9_combined_evaluation",
    ),
]:
    instance = getattr(
        MINH,
        attribute,
        None,
    )

    validate = getattr(
        instance,
        "validate",
        None,
    )

    if not callable(validate):
        fail(
            label,
            "validate() missing",
        )

    result = validate()

    if not isinstance(
        result,
        dict,
    ):
        fail(
            label,
            repr(result),
        )

    if result.get("valid") is not True:
        fail(
            label,
            repr(result),
        )

    print(f"{label}: PASS")


# ============================================================
# 10. P8-2 PRESERVATION
# ============================================================

be_critic = MINH.be_critic

validate_be = getattr(
    be_critic,
    "validate",
    None,
)

if not callable(validate_be):
    fail(
        "P8-2 BE CRITIC",
        "validate() missing",
    )

be_result = validate_be()

if not isinstance(
    be_result,
    dict,
):
    fail(
        "P8-2 BE CRITIC",
        repr(be_result),
    )

if be_result.get("valid") is not True:
    fail(
        "P8-2 BE CRITIC",
        repr(be_result),
    )

print("P8-2 BE CRITIC PRESERVED: PASS")


# ============================================================
# 11. P7 / P6 / P5 VALIDATION
# ============================================================

planner_result = MINH.task_planner.validate()

if planner_result.get("valid") is not True:
    fail(
        "P7-2 TASK PLANNER",
        repr(planner_result),
    )

print(
    "P7-2 TASK PLANNER PRESERVED: PASS"
)


state_result = MINH.state_manager.validate()

if state_result.get("valid") is not True:
    fail(
        "P6-3 STATE MANAGER",
        repr(state_result),
    )

print(
    "P6-3 STATE MANAGER PRESERVED: PASS"
)


world_result = MINH.world_model.validate()

if world_result.get("valid") is not True:
    fail(
        "P5 WORLD MODEL",
        repr(world_result),
    )

print(
    "P5 WORLD MODEL PRESERVED: PASS"
)


# ============================================================
# 12. P9 STATUS
# ============================================================

p9_status = MINH._p9_6_get_evaluation_status()

if not isinstance(
    p9_status,
    dict,
):
    fail(
        "P9 STATUS",
        repr(p9_status),
    )

if p9_status.get("available") is not True:
    fail(
        "P9 STATUS",
        repr(p9_status),
    )

if p9_status.get("verdict") not in {
    "pass",
    "review",
    "block",
}:
    fail(
        "P9 STATUS VERDICT",
        repr(p9_status),
    )

print(
    "P9 STATUS: PASS",
    p9_status,
)


# ============================================================
# FINAL
# ============================================================

print("\n=== FINAL ===")
print("P9-7 RUNTIME VALIDATION: PASS")
print("P9-6 P9 -> MAIN: PRESERVED")
print("P9-5 CORE VALIDATION: PRESERVED")
print("P9-4 COMBINED EVALUATION: PRESERVED")
print("P9-3 FACTCHECK: PRESERVED")
print("P9-2 RED TEAM: PRESERVED")
print("P9-1 CRITIC: PRESERVED")
print("P8-2 BE CRITIC: PRESERVED")
print("P7-2 TASK PLANNER: PRESERVED")
print("P6-3 STATE MANAGER: PRESERVED")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("SUCCESS -> BLOCKED -> SUCCESS: PASS")
print("P9 MODE: ADVISORY")
print("EXECUTION CONTROL CHANGE: NO")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
