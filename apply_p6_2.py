from pathlib import Path
import py_compile
import shutil
import sys

APP = Path(__file__).resolve().parent
MAIN = APP / "main.py"
BACKUP = APP / "main.py.before_p6_2_state_manager"

print("=== P6-2 STATE MANAGER -> MAIN ===")

if not MAIN.exists():
    print("MAIN.PY NOT FOUND")
    raise SystemExit(1)

# ============================================================
# BACKUP
# ============================================================

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)
    print("BACKUP CREATED")
else:
    print("BACKUP EXISTS")

text = MAIN.read_text(encoding="utf-8-sig")

original = text


def replace_once(source, old, new, label):
    count = source.count(old)

    if count != 1:
        print(f"{label}: FAIL (matches={count})")
        raise SystemExit(1)

    print(f"{label}: PASS")
    return source.replace(old, new, 1)


# ============================================================
# 1. STATE MANAGER INIT
# ============================================================

old = '''        # GOAL_MANAGER_V6_INIT
        try:
            from goal_manager import create_goal_manager
            self.goal_manager = create_goal_manager()
        except Exception as exc:
            self.goal_manager = None
            log("GOAL MANAGER INIT ERROR: " + repr(exc))
'''

new = '''        # P6_STATE_MANAGER_INIT
        # State Manager chi quan ly application/session state.
        # Khong route, khong execute, khong goi Ollama/Web.
        try:
            from state_manager import create_state_manager

            self.state_manager = create_state_manager(
                {
                    "session": "MINH MINI",
                    "status": "idle",
                    "turn_count": 0,
                    "original_message": None,
                    "completed_message": None,
                    "decision": None,
                    "execution_result": None,
                    "verification": None,
                }
            )

        except Exception as exc:
            self.state_manager = None
            log(
                "STATE MANAGER INIT ERROR: "
                + repr(exc)
            )

        # GOAL_MANAGER_V6_INIT
        try:
            from goal_manager import create_goal_manager
            self.goal_manager = create_goal_manager()
        except Exception as exc:
            self.goal_manager = None
            log("GOAL MANAGER INIT ERROR: " + repr(exc))
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_INIT",
)


# ============================================================
# 2. STATUS
# ============================================================

old = '''            "controller": self.controller is not None,
            "router_guard": (
                router_guard is not None
            ),
'''

new = '''            "controller": self.controller is not None,
            "state_manager": (
                self.state_manager is not None
            ),
            "state_manager_valid": (
                self.state_manager.validate()["valid"]
                if self.state_manager is not None
                else False
            ),
            "router_guard": (
                router_guard is not None
            ),
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_STATUS",
)


# ============================================================
# 3. PROCESS START STATE
# ============================================================

old = '''        self.turn_count += 1


        # P45_VERIFY_STATE_LIFECYCLE_V2
        self.last_execution_verification = None

        log(
            f"USER: {original}"
        )
'''

new = '''        self.turn_count += 1

        # P6_STATE_MANAGER_TURN_START
        # Cap nhat state theo turn hien tai.
        # Khong thay doi routing/execution.
        if self.state_manager is not None:
            try:
                self.state_manager.update(
                    {
                        "status": "processing",
                        "turn_count": self.turn_count,
                        "original_message": original,
                        "completed_message": None,
                        "decision": None,
                        "execution_result": None,
                        "verification": None,
                    }
                )
            except Exception as exc:
                log(
                    "STATE MANAGER TURN START ERROR: "
                    + repr(exc)
                )

        # P45_VERIFY_STATE_LIFECYCLE_V2
        self.last_execution_verification = None

        log(
            f"USER: {original}"
        )
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_TURN_START",
)


# ============================================================
# 4. AFTER COMMAND COMPLETION
# ============================================================

old = '''        if not completed:
            completed = original

        # ----------------------------------------------------
        # 2. BRAIN
'''

new = '''        if not completed:
            completed = original

        # P6_STATE_MANAGER_COMPLETED_INPUT
        if self.state_manager is not None:
            try:
                self.state_manager.update(
                    {
                        "completed_message": completed,
                    }
                )
            except Exception as exc:
                log(
                    "STATE MANAGER INPUT UPDATE ERROR: "
                    + repr(exc)
                )

        # ----------------------------------------------------
        # 2. BRAIN
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_COMPLETED_INPUT",
)


# ============================================================
# 5. AFTER DECISION / ROUTING
# ============================================================

old = '''            if route_intent:
                decision = route

        # ----------------------------------------------------
        # 4. CLARIFICATION
'''

new = '''            if route_intent:
                decision = route

        # P6_STATE_MANAGER_DECISION
        # Store isolated decision state only.
        if self.state_manager is not None:
            try:
                if isinstance(decision, dict):
                    state_decision = dict(decision)
                elif hasattr(decision, "__dict__"):
                    state_decision = dict(decision.__dict__)
                else:
                    state_decision = str(decision)

                self.state_manager.update(
                    {
                        "decision": state_decision,
                    }
                )

            except Exception as exc:
                log(
                    "STATE MANAGER DECISION UPDATE ERROR: "
                    + repr(exc)
                )

        # ----------------------------------------------------
        # 4. CLARIFICATION
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_DECISION",
)


# ============================================================
# 6. CLARIFICATION STATE
# ============================================================

old = '''            answer = self.make_clarification(
                completed,
                decision,
            )

            answer = guard_answer(
'''

new = '''            # P6_STATE_MANAGER_BLOCKED
            if self.state_manager is not None:
                try:
                    self.state_manager.update(
                        {
                            "status": "blocked",
                            "execution_result": None,
                            "verification": dict(
                                self.last_execution_verification
                            ),
                        }
                    )
                except Exception as exc:
                    log(
                        "STATE MANAGER BLOCKED UPDATE ERROR: "
                        + repr(exc)
                    )

            answer = self.make_clarification(
                completed,
                decision,
            )

            answer = guard_answer(
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_BLOCKED",
)


# ============================================================
# 7. AFTER EXECUTION + VERIFY
# ============================================================

old = '''            log(
                "EXECUTION VERIFY ERROR: "
                + traceback.format_exc()
            )

        # P5_WORLD_MODEL_OBSERVATION
'''

new = '''            log(
                "EXECUTION VERIFY ERROR: "
                + traceback.format_exc()
            )

        # P6_STATE_MANAGER_EXECUTION_RESULT
        # State-only update. Khong execute lai.
        if self.state_manager is not None:
            try:
                if isinstance(execution_result, dict):
                    state_execution_result = dict(
                        execution_result
                    )
                elif hasattr(execution_result, "__dict__"):
                    state_execution_result = dict(
                        execution_result.__dict__
                    )
                else:
                    state_execution_result = execution_result

                state_verification = (
                    dict(verification)
                    if isinstance(verification, dict)
                    else verification
                )

                success = get_decision_value(
                    execution_result,
                    "success",
                    None,
                )

                state_status = (
                    "completed"
                    if success is True
                    else "failed"
                    if success is False
                    else "unknown"
                )

                self.state_manager.update(
                    {
                        "status": state_status,
                        "execution_result": (
                            state_execution_result
                        ),
                        "verification": state_verification,
                    }
                )

            except Exception as exc:
                log(
                    "STATE MANAGER EXECUTION UPDATE ERROR: "
                    + repr(exc)
                )

        # P5_WORLD_MODEL_OBSERVATION
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_EXECUTION_RESULT",
)


# ============================================================
# 8. FINAL STATE BEFORE RETURN
# ============================================================

old = '''        log(
            f"ASSISTANT: {answer}"
        )

        return answer

    # --------------------------------------------------------
    # CLARIFICATION
'''

new = '''        # P6_STATE_MANAGER_FINAL
        if self.state_manager is not None:
            try:
                self.state_manager.update(
                    {
                        "status": (
                            "completed"
                            if (
                                isinstance(
                                    verification,
                                    dict,
                                )
                                and verification.get(
                                    "verified"
                                ) is True
                            )
                            else self.state_manager.get(
                                "status",
                                "unknown",
                            )
                        ),
                        "verification": (
                            dict(verification)
                            if isinstance(
                                verification,
                                dict,
                            )
                            else verification
                        ),
                    }
                )
            except Exception as exc:
                log(
                    "STATE MANAGER FINAL UPDATE ERROR: "
                    + repr(exc)
                )

        log(
            f"ASSISTANT: {answer}"
        )

        return answer

    # --------------------------------------------------------
    # CLARIFICATION
'''

text = replace_once(
    text,
    old,
    new,
    "STATE_MANAGER_FINAL",
)


# ============================================================
# WRITE
# ============================================================

if text == original:
    print("NO CHANGES")
    raise SystemExit(1)

MAIN.write_text(
    text,
    encoding="utf-8",
    newline="",
)

print("")
print("MAIN.PY MODIFIED: YES")


# ============================================================
# COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
    print("MAIN_COMPILE: PASS")
except Exception:
    print("MAIN_COMPILE: FAIL")
    raise


try:
    state_file = APP / "state_manager.py"

    py_compile.compile(
        str(state_file),
        doraise=True,
    )

    print("STATE_MANAGER_COMPILE: PASS")

except Exception:
    print("STATE_MANAGER_COMPILE: FAIL")
    raise


# ============================================================
# IMPORT
# ============================================================

try:
    import importlib

    if str(APP) not in sys.path:
        sys.path.insert(0, str(APP))

    import main
    importlib.reload(main)

    print("MAIN_IMPORT: PASS")

    if getattr(main.MINH, "state_manager", None) is None:
        print("STATE_MANAGER_INSTANCE: FAIL")
        raise SystemExit(1)

    print("STATE_MANAGER_INSTANCE: PASS")

    state = main.MINH.state_manager.get_state()

    required = {
        "session",
        "status",
        "turn_count",
        "original_message",
        "completed_message",
        "decision",
        "execution_result",
        "verification",
    }

    if required.issubset(state.keys()):
        print("STATE_SCHEMA: PASS")
    else:
        print("STATE_SCHEMA: FAIL")
        print("STATE KEYS:", sorted(state.keys()))
        raise SystemExit(1)

except Exception:
    print("MAIN_IMPORT: FAIL")
    raise


print("")
print("=== P6-2 PATCH COMPLETE ===")
print("P6-2 STATE MANAGER -> MAIN: PASS")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("AUTO GIT COMMIT: NO")
print("BACKUP:", BACKUP.name)