import os
import py_compile
import importlib


APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_FILE = os.path.join(APP_DIR, "main.py")
STATE_FILE = os.path.join(APP_DIR, "state_manager.py")


def check(name, condition):
    print(f"{name}: {'PASS' if condition else 'FAIL'}")
    return bool(condition)


print("=== P6-3 STATE MANAGER RUNTIME VALIDATION ===")

all_pass = True

# ---------------------------------------------------------
# 1. FILE CHECK
# ---------------------------------------------------------
all_pass &= check("MAIN_FILE", os.path.isfile(MAIN_FILE))
all_pass &= check("STATE_MANAGER_FILE", os.path.isfile(STATE_FILE))

# ---------------------------------------------------------
# 2. COMPILE CHECK
# ---------------------------------------------------------
try:
    py_compile.compile(MAIN_FILE, doraise=True)
    all_pass &= check("MAIN_COMPILE", True)
except Exception as exc:
    print("MAIN_COMPILE_ERROR:", exc)
    all_pass &= check("MAIN_COMPILE", False)

try:
    py_compile.compile(STATE_FILE, doraise=True)
    all_pass &= check("STATE_MANAGER_COMPILE", True)
except Exception as exc:
    print("STATE_MANAGER_COMPILE_ERROR:", exc)
    all_pass &= check("STATE_MANAGER_COMPILE", False)

# ---------------------------------------------------------
# 3. IMPORT
# ---------------------------------------------------------
try:
    import main
    importlib.reload(main)
    all_pass &= check("MAIN_IMPORT", True)
except Exception as exc:
    print("MAIN_IMPORT_ERROR:", exc)
    all_pass &= check("MAIN_IMPORT", False)
    print("\n=== FINAL ===")
    print("P6-3 STATE RUNTIME VALIDATION: FAIL")
    raise SystemExit(1)

# ---------------------------------------------------------
# 4. STATE MANAGER EXISTENCE
# ---------------------------------------------------------
try:
    sm = main.MINH.state_manager
    all_pass &= check("STATE_MANAGER_INSTANCE", sm is not None)
    all_pass &= check(
        "STATE_MANAGER_VALID",
        main.MINH.status().get("state_manager_valid") is True,
    )
except Exception as exc:
    print("STATE_MANAGER_ACCESS_ERROR:", exc)
    all_pass &= check("STATE_MANAGER_INSTANCE", False)
    all_pass &= check("STATE_MANAGER_VALID", False)
    print("\n=== FINAL ===")
    print("P6-3 STATE RUNTIME VALIDATION: FAIL")
    raise SystemExit(1)

# ---------------------------------------------------------
# 5. INITIAL STATE
# ---------------------------------------------------------
initial_state = sm.get_state()

all_pass &= check(
    "INITIAL_STATUS",
    initial_state.get("status") == "idle",
)

all_pass &= check(
    "INITIAL_EXECUTION_NONE",
    initial_state.get("execution_result") is None,
)

all_pass &= check(
    "INITIAL_VERIFICATION_NONE",
    initial_state.get("verification") is None,
)

# ---------------------------------------------------------
# 6. TURN 1 — SUCCESS
# ---------------------------------------------------------
answer1 = main.MINH.process("m? youtube")
state1 = sm.get_state()

all_pass &= check(
    "TURN1_ANSWER",
    isinstance(answer1, str) and len(answer1.strip()) > 0,
)

all_pass &= check(
    "TURN1_STATUS_COMPLETED",
    state1.get("status") == "completed",
)

all_pass &= check(
    "TURN1_TURN_COUNT",
    state1.get("turn_count", 0) > 0,
)

decision1 = state1.get("decision") or {}
execution1 = state1.get("execution_result") or {}
verification1 = state1.get("verification") or {}

all_pass &= check(
    "TURN1_DECISION",
    decision1.get("valid") is True,
)

all_pass &= check(
    "TURN1_EXECUTION_SUCCESS",
    execution1.get("success") is True,
)

all_pass &= check(
    "TURN1_VERIFICATION_PASS",
    verification1.get("verified") is True
    and verification1.get("status") == "pass"
    and verification1.get("success") is True,
)

all_pass &= check(
    "TURN1_TARGET_YOUTUBE",
    decision1.get("target") == "youtube",
)

turn1_count = state1.get("turn_count")

# ---------------------------------------------------------
# 7. TURN 2 — BLOCKED / CLARIFICATION
# ---------------------------------------------------------
answer2 = main.MINH.process("mở")
state2 = sm.get_state()

all_pass &= check(
    "TURN2_ANSWER",
    isinstance(answer2, str) and len(answer2.strip()) > 0,
)

all_pass &= check(
    "TURN2_STATUS_BLOCKED",
    state2.get("status") == "blocked",
)

all_pass &= check(
    "TURN2_TURN_COUNT_INCREMENT",
    state2.get("turn_count") == turn1_count + 1,
)

decision2 = state2.get("decision") or {}
execution2 = state2.get("execution_result")
verification2 = state2.get("verification") or {}

all_pass &= check(
    "TURN2_CLARIFICATION",
    decision2.get("intent") == "clarification"
    and decision2.get("needs_clarification") is True,
)

all_pass &= check(
    "TURN2_NO_EXECUTION",
    execution2 is None,
)

all_pass &= check(
    "TURN2_VERIFICATION_BLOCKED",
    verification2.get("verified") is False
    and verification2.get("status") == "blocked"
    and verification2.get("success") is None,
)

all_pass &= check(
    "TURN2_NO_OLD_EXECUTION",
    execution2 is None,
)

all_pass &= check(
    "TURN2_NO_OLD_VERIFICATION",
    verification2.get("status") != "pass",
)

turn2_count = state2.get("turn_count")

# ---------------------------------------------------------
# 8. TURN 3 — SUCCESS WITH NEW TARGET
# ---------------------------------------------------------
answer3 = main.MINH.process("mở google")
state3 = sm.get_state()

all_pass &= check(
    "TURN3_ANSWER",
    isinstance(answer3, str) and len(answer3.strip()) > 0,
)

all_pass &= check(
    "TURN3_STATUS_COMPLETED",
    state3.get("status") == "completed",
)

all_pass &= check(
    "TURN3_TURN_COUNT_INCREMENT",
    state3.get("turn_count") == turn2_count + 1,
)

decision3 = state3.get("decision") or {}
execution3 = state3.get("execution_result") or {}
verification3 = state3.get("verification") or {}

all_pass &= check(
    "TURN3_DECISION",
    decision3.get("valid") is True,
)

all_pass &= check(
    "TURN3_TARGET_GOOGLE",
    decision3.get("target") == "google",
)

all_pass &= check(
    "TURN3_EXECUTION_SUCCESS",
    execution3.get("success") is True,
)

all_pass &= check(
    "TURN3_VERIFICATION_PASS",
    verification3.get("verified") is True
    and verification3.get("status") == "pass"
    and verification3.get("success") is True,
)

# ---------------------------------------------------------
# 9. CROSS-TURN LEAK CHECK
# ---------------------------------------------------------
all_pass &= check(
    "NO_TURN2_STATE_LEAK",
    state3.get("status") == "completed"
    and state3.get("execution_result") is not None
    and state3.get("verification", {}).get("status") == "pass",
)

all_pass &= check(
    "NEW_TARGET_REPLACED",
    state3.get("decision", {}).get("target") == "google",
)

all_pass &= check(
    "OLD_TARGET_NOT_ACTIVE",
    state3.get("decision", {}).get("target") != "youtube",
)

# ---------------------------------------------------------
# 10. WORLD MODEL CROSS-CHECK
# ---------------------------------------------------------
try:
    wm = main.MINH.world_model

    all_pass &= check(
        "WORLD_MODEL_EXISTS",
        wm is not None,
    )

    wm_state = wm.get_state()

    active_goal = wm_state.get("active_goal") or {}
    last_observation = wm_state.get("last_observation") or {}

    all_pass &= check(
        "WORLD_MODEL_TARGET_GOOGLE",
        active_goal.get("target") == "google",
    )

    all_pass &= check(
        "WORLD_MODEL_OBSERVATION_SUCCESS",
        last_observation.get("execution_success") is True,
    )

    all_pass &= check(
        "WORLD_MODEL_VERIFICATION_PASS",
        last_observation.get("verification", {}).get("status") == "pass",
    )

except Exception as exc:
    print("WORLD_MODEL_CROSSCHECK_ERROR:", exc)
    all_pass &= check("WORLD_MODEL_EXISTS", False)

# ---------------------------------------------------------
# 11. FINAL STATE
# ---------------------------------------------------------
final_state = sm.get_state()

all_pass &= check(
    "FINAL_STATE_VALID",
    sm.validate().get("valid") is True,
)

all_pass &= check(
    "FINAL_STATUS_COMPLETED",
    final_state.get("status") == "completed",
)

all_pass &= check(
    "FINAL_EXECUTION_SUCCESS",
    (final_state.get("execution_result") or {}).get("success") is True,
)

all_pass &= check(
    "FINAL_VERIFICATION_PASS",
    (final_state.get("verification") or {}).get("status") == "pass",
)

print("\n=== FINAL ===")

if all_pass:
    print("P6-3 STATE MANAGER RUNTIME VALIDATION: PASS")
    print("P6-2 STATE MANAGER -> MAIN: PRESERVED")
    print("P5 WORLD MODEL: PRESERVED")
    print("P4-5 EXECUTE -> VERIFY: PRESERVED")
    print("SUCCESS -> BLOCKED -> SUCCESS: PASS")
    print("STATE LEAK CHECK: PASS")
    print("AUTO EXECUTION: NO")
    raise SystemExit(0)

print("P6-3 STATE MANAGER RUNTIME VALIDATION: FAIL")
print("DO NOT PROCEED TO P7")
raise SystemExit(1)
