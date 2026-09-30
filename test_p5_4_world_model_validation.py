from pathlib import Path
import py_compile
import importlib
import traceback

APP = Path(__file__).resolve().parent
RESULTS = []

def check(name, condition):
    ok = bool(condition)
    RESULTS.append((name, ok))
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
    return ok

print("=== P5-4 WORLD MODEL VALIDATION ===")

try:
    world_model_file = APP / "world_model.py"
    main_file = APP / "main.py"

    check("WORLD_MODEL_FILE", world_model_file.exists())
    check("MAIN_FILE", main_file.exists())

    py_compile.compile(str(world_model_file), doraise=True)
    check("WORLD_MODEL_COMPILE", True)

    py_compile.compile(str(main_file), doraise=True)
    check("MAIN_COMPILE", True)

    import world_model
    importlib.reload(world_model)

    check("WORLD_MODEL_IMPORT", True)

    wm = world_model.create_world_model()

    state0 = wm.get_state()
    check("INITIAL_STATE", isinstance(state0, dict))

    goal = {
        "text": "mở youtube",
        "intent": "action",
        "action": "open",
        "target": "youtube",
        "status": "active",
    }

    wm.set_goal(goal)
    state1 = wm.get_state()

    check(
        "GOAL_STATE",
        state1.get("active_goal", {}).get("target") == "youtube"
    )

    wm.set_fact("test_fact", "P5-4")
    state2 = wm.get_state()

    check(
        "FACT_STORAGE",
        state2.get("known_facts", {}).get("test_fact") == "P5-4"
    )

    check(
        "FACT_READ",
        wm.get_fact("test_fact") == "P5-4"
    )

    wm.set_environment("test_environment", "P5-4")
    state3 = wm.get_state()

    check(
        "ENVIRONMENT_STATE",
        state3.get("environment_state", {}).get("test_environment") == "P5-4"
    )

    observation = {
        "message": "mở youtube",
        "target": "youtube",
        "answer_present": True,
        "execution_success": True,
        "verification": {
            "verified": True,
            "status": "pass",
            "success": True,
        },
    }

    wm.record_observation(observation)
    state4 = wm.get_state()

    check(
        "OBSERVATION",
        state4.get("last_observation", {}).get("target") == "youtube"
    )

    snapshot = wm.snapshot()

    snapshot["active_goal"]["target"] = "CHANGED"

    state5 = wm.get_state()

    check(
        "SNAPSHOT_ISOLATION",
        state5.get("active_goal", {}).get("target") == "youtube"
    )

    validation = wm.validate()

    check(
        "VALIDATION",
        bool(validation)
    )

    print("")
    print("=== MAIN INTEGRATION ===")

    import main
    importlib.reload(main)

    check(
        "MAIN_IMPORT",
        hasattr(main, "MINH")
    )

    check(
        "MAIN_WORLD_MODEL",
        getattr(main.MINH, "world_model", None) is not None
    )

    print("")
    print("=== RUNTIME REGRESSION P5-3 / P4-5 ===")

    result1 = main.MINH.process("m? youtube")
    state_turn1 = main.MINH.world_model.get_state()

    verify1 = getattr(main.MINH, "last_execution_verification", {})

    check(
        "TURN1_SUCCESS",
        bool(verify1.get("verified")) and
        verify1.get("status") == "pass" and
        verify1.get("success") is True
    )

    check(
        "TURN1_TARGET",
        state_turn1.get("active_goal", {}).get("target") == "youtube"
    )

    check(
        "TURN1_OBSERVATION",
        state_turn1.get("last_observation", {}).get("target") == "youtube"
    )

    result2 = main.MINH.process("m?")
    state_turn2 = main.MINH.world_model.get_state()

    verify2 = getattr(main.MINH, "last_execution_verification", {})

    check(
        "TURN2_BLOCKED",
        verify2.get("status") == "blocked" and
        verify2.get("success") is None
    )

    check(
        "TURN2_NO_STATE_LEAK",
        state_turn2.get("active_goal", {}).get("status") == "blocked" and
        state_turn2.get("active_goal", {}).get("target", "") == "" and
        state_turn2.get("last_observation", {}).get("execution_success") is None
    )

    check(
        "TURN2_OBSERVATION_BLOCKED",
        state_turn2.get("last_observation", {}).get("verification", {}).get("status")
        == "blocked"
    )

    result3 = main.MINH.process("m? google")
    state_turn3 = main.MINH.world_model.get_state()

    verify3 = getattr(main.MINH, "last_execution_verification", {})

    check(
        "TURN3_SUCCESS",
        bool(verify3.get("verified")) and
        verify3.get("status") == "pass" and
        verify3.get("success") is True
    )

    check(
        "TURN3_NEW_TARGET",
        state_turn3.get("active_goal", {}).get("target") == "google"
    )

    check(
        "TURN3_COMPLETED",
        state_turn3.get("active_goal", {}).get("status") == "completed"
    )

    check(
        "TURN3_OBSERVATION",
        state_turn3.get("last_observation", {}).get("target") == "google"
    )

except Exception:
    print("")
    print("=== ERROR ===")
    traceback.print_exc()
    print("")
    print("P5-4 WORLD MODEL VALIDATION: FAIL")
    raise SystemExit(1)

print("")
print("=== FINAL ===")

failed = [name for name, ok in RESULTS if not ok]

if failed:
    print("FAILED CHECKS:")
    for name in failed:
        print("-", name)
    print("P5-4 WORLD MODEL VALIDATION: FAIL")
    raise SystemExit(1)

print("P5-4 WORLD MODEL VALIDATION: PASS")
print("P5-1 WORLD MODEL CORE: PASS")
print("P5-2 WORLD MODEL INTEGRATION: PASS")
print("P5-3 WORLD MODEL STATE LEAK: PASS")
print("P4-5 EXECUTE -> VERIFY: PASS")
print("AUTO EXECUTION: NO")
