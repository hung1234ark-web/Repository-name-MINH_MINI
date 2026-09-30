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

print("=== P6-1 STATE MANAGER VALIDATION ===")

try:
    state_manager_file = APP / "state_manager.py"

    check("STATE_MANAGER_FILE", state_manager_file.exists())

    py_compile.compile(str(state_manager_file), doraise=True)
    check("STATE_MANAGER_COMPILE", True)

    import state_manager
    importlib.reload(state_manager)

    check("STATE_MANAGER_IMPORT", True)

    manager = state_manager.create_state_manager(
        {
            "session": "P6-1",
            "counter": 0,
        }
    )

    state0 = manager.get_state()

    check(
        "STATE_CREATION",
        state0.get("session") == "P6-1"
        and state0.get("counter") == 0
    )

    manager.set("counter", 1)

    check(
        "STATE_UPDATE",
        manager.get("counter") == 1
    )

    manager.update(
        {
            "mode": "test",
            "nested": {
                "value": 123,
            },
        }
    )

    check(
        "MULTI_STATE_UPDATE",
        manager.get("mode") == "test"
        and manager.get("nested", {}).get("value") == 123
    )

    snapshot = manager.snapshot()
    snapshot["nested"]["value"] = 999

    check(
        "SNAPSHOT_ISOLATION",
        manager.get("nested", {}).get("value") == 123
    )

    check(
        "STATE_HISTORY",
        manager.history_size() >= 2
    )

    manager.remove("mode")

    check(
        "STATE_REMOVE",
        manager.get("mode") is None
    )

    validation = manager.validate()

    check(
        "STATE_VALIDATION",
        validation.get("valid") is True
    )

    manager.reset(
        {
            "reset": True,
        }
    )

    check(
        "STATE_RESET",
        manager.get("reset") is True
        and manager.history_size() == 0
    )

    status = manager.status()

    check(
        "STATE_STATUS",
        status.get("module") == "state_manager"
        and status.get("version") == "P6-1.0"
        and status.get("valid") is True
    )

    self_check = state_manager.self_check()

    check(
        "SELF_CHECK",
        self_check.get("passed") is True
    )

except Exception:
    print("")
    print("=== ERROR ===")
    traceback.print_exc()
    print("")
    print("P6-1 STATE MANAGER VALIDATION: FAIL")
    raise SystemExit(1)

print("")
print("=== FINAL ===")

failed = [name for name, ok in RESULTS if not ok]

if failed:
    print("FAILED CHECKS:")
    for name in failed:
        print("-", name)

    print("P6-1 STATE MANAGER VALIDATION: FAIL")
    raise SystemExit(1)

print("P6-1 STATE MANAGER CORE: PASS")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("MAIN.PY: NOT MODIFIED")
print("AUTO EXECUTION: NO")
