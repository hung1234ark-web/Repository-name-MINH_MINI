from pathlib import Path
import py_compile
import shutil

BASE = Path(__file__).resolve().parent
MAIN = BASE / "main.py"

text = MAIN.read_text(encoding="utf-8")

if "from world_model import create_world_model" in text:
    raise SystemExit("ABORT: World Model integration already exists.")

backup = BASE / "main.py.before_p5_2_world_model"

if not backup.exists():
    shutil.copy2(MAIN, backup)
    print(f"BACKUP CREATED: {backup}")
else:
    print(f"BACKUP EXISTS: {backup}")

# ------------------------------------------------------------
# 1. INIT
# ------------------------------------------------------------

needle = """        # GOAL_MANAGER_V6_INIT
"""

insert = """        # P5_WORLD_MODEL_INIT
        try:
            from world_model import create_world_model
            self.world_model = create_world_model()
        except Exception as exc:
            self.world_model = None
            log("WORLD MODEL INIT ERROR: " + repr(exc))

"""

if needle not in text:
    raise SystemExit("ABORT: INIT anchor not found.")

text = text.replace(
    needle,
    insert + needle,
    1,
)

# ------------------------------------------------------------
# 2. STATE UPDATE AFTER EXECUTION + VERIFY
# ------------------------------------------------------------

needle = """        # GOAL_MANAGER_V6_RESULT
"""

insert = """        # P5_WORLD_MODEL_OBSERVATION
        if self.world_model is not None:
            try:
                goal_data = None
                task_data = None

                if self.goal_manager is not None:
                    get_current = getattr(
                        self.goal_manager,
                        "get_current",
                        None,
                    )

                    if callable(get_current):
                        current_goal = get_current()

                        if current_goal is not None:
                            if hasattr(current_goal, "to_dict"):
                                goal_data = current_goal.to_dict()
                            elif hasattr(current_goal, "__dict__"):
                                goal_data = dict(
                                    current_goal.__dict__
                                )
                            elif isinstance(current_goal, dict):
                                goal_data = dict(current_goal)

                observation = {
                    "message": completed,
                    "intent": get_decision_value(
                        decision,
                        "intent",
                        "",
                    ),
                    "tool": get_decision_value(
                        decision,
                        "tool",
                        "",
                    ),
                    "action": get_decision_value(
                        decision,
                        "action",
                        "",
                    ),
                    "target": get_decision_value(
                        decision,
                        "target",
                        "",
                    ),
                    "answer_present": bool(answer),
                    "execution_success": get_decision_value(
                        execution_result,
                        "success",
                        None,
                    ),
                    "verification": (
                        dict(verification)
                        if isinstance(verification, dict)
                        else verification
                    ),
                }

                self.world_model.set_goal(
                    goal_data
                )

                self.world_model.record_observation(
                    observation
                )

            except Exception as exc:
                log(
                    "WORLD MODEL UPDATE ERROR: "
                    + repr(exc)
                )

"""

if needle not in text:
    raise SystemExit(
        "ABORT: execution result anchor not found."
    )

text = text.replace(
    needle,
    insert + needle,
    1,
)

MAIN.write_text(
    text,
    encoding="utf-8",
)

# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

py_compile.compile(
    str(MAIN),
    doraise=True,
)

print("MAIN.PY WRITE       : PASS")
print("COMPILE              : PASS")

# Import + integration check
import main

instance = main.MINH

if getattr(instance, "world_model", None) is None:
    raise SystemExit(
        "FAIL: World Model was not initialized."
    )

status = instance.world_model.status()

if status.get("module") != "world_model":
    raise SystemExit(
        "FAIL: World Model status invalid."
    )

print("IMPORT               : PASS")
print("WORLD MODEL INIT     : PASS")
print("WORLD MODEL STATUS   : PASS")

print("=" * 64)
print("P5-2 WORLD MODEL INTEGRATION: PASS")
print("=" * 64)
print("MAIN.PY MODIFIED     : YES")
print("P4-5 EXECUTION CODE : UNCHANGED")
print("P4-5 VERIFY CODE    : UNCHANGED")
print("AUTO EXECUTION      : NO")
print("=" * 64)
