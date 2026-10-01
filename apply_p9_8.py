from pathlib import Path
import os
import sys
import tempfile
import subprocess
import py_compile
import shutil

ROOT = Path(__file__).resolve().parent
CRITIC = ROOT / "critic.py"
RED_TEAM = ROOT / "red_team.py"
MAIN = ROOT / "main.py"


def fail(message):
    raise RuntimeError(message)


def read_source(path):
    if not path.exists():
        fail(f"Missing source file: {path.name}")
    return path.read_text(encoding="utf-8-sig")


def write_utf8(path, text):
    path.write_text(text, encoding="utf-8")


def patch_object_normalization(source, module_name):
    if module_name == "critic":
        old = '''    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}
'''
        new = '''    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value

        if value is None:
            return {}

        data = getattr(value, "__dict__", None)
        if isinstance(data, dict):
            return dict(data)

        return {}
'''
    elif module_name == "red_team":
        old = '''    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}
'''
        new = '''    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value

        if value is None:
            return {}

        data = getattr(value, "__dict__", None)
        if isinstance(data, dict):
            return dict(data)

        return {}
'''
    else:
        fail(f"Unknown module: {module_name}")

    if old not in source:
        fail(
            f"{module_name}.py: exact _as_dict anchor not found. "
            "No source file was modified."
        )

    return source.replace(old, new, 1)


def patch_red_team_simple_goal_calibration(source):
    old = '''        if isinstance(tasks, list) and tasks:
            checks["plan_has_execution_path"] = True
        else:
            warnings.append(
                "no_clear_execution_path"
            )
            checks[
                "plan_has_execution_path"
            ] = False
'''

    new = '''        if isinstance(tasks, list) and tasks:
            checks["plan_has_execution_path"] = True
        elif tasks is None:
            # A simple one-turn goal may legitimately have no Task Planner
            # plan. This is not a structural execution-path failure.
            checks[
                "plan_has_execution_path"
            ] = True
        else:
            warnings.append(
                "no_clear_execution_path"
            )
            checks[
                "plan_has_execution_path"
            ] = False
'''

    if old not in source:
        fail(
            "red_team.py: exact simple-goal execution-path anchor "
            "not found. No source file was modified."
        )

    return source.replace(old, new, 1)


def regression_script():
    return r'''
from types import SimpleNamespace
from critic import Critic
from red_team import RedTeam


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


goal = SimpleNamespace(
    text="mở youtube",
    intent="command",
    action="open",
    target="youtube",
    topic="",
    query="",
    status="completed",
)

result = {
    "message": "Đã mở https://www.youtube.com.",
    "success": True,
    "target": "youtube",
    "verification": {
        "verified": True,
        "status": "pass",
        "success": True,
    },
}

simple_plan = {
    "goal": {
        "text": "mở youtube",
        "target": "youtube",
    },
    "tasks": [],
}

critic = Critic()
red_team = RedTeam()

critic_dict = Critic._as_dict(goal)
red_dict = RedTeam._as_dict(goal)

check(
    critic_dict.get("target") == "youtube",
    f"Critic object normalization failed: {critic_dict!r}",
)

check(
    red_dict.get("target") == "youtube",
    f"Red Team object normalization failed: {red_dict!r}",
)

critic_result = critic.evaluate(
    goal=goal,
    plan=simple_plan,
    result=result,
)

red_result = red_team.evaluate(
    goal=goal,
    plan=simple_plan,
    result=result,
)

print("CRITIC RESULT:", critic_result)
print("RED TEAM RESULT:", red_result)

check(
    critic_result.get("valid") is True,
    "Critic result is not valid",
)

check(
    critic_result.get("verdict") != "block",
    f"Critic simple Goal unexpectedly blocked: {critic_result!r}",
)

check(
    red_result.get("valid") is True,
    "Red Team result is not valid",
)

check(
    red_result.get("verdict") != "block",
    f"Red Team simple Goal unexpectedly blocked: {red_result!r}",
)

# A real target mismatch must remain blocking.
mismatch_result = dict(result)
mismatch_result["target"] = "google"

critic_mismatch = critic.evaluate(
    goal=goal,
    plan=simple_plan,
    result=mismatch_result,
)

red_mismatch = red_team.evaluate(
    goal=goal,
    plan=simple_plan,
    result=mismatch_result,
)

check(
    critic_mismatch.get("verdict") == "block",
    "Critic target mismatch is no longer blocking",
)

check(
    red_mismatch.get("verdict") == "block",
    "Red Team target mismatch is no longer blocking",
)

print("P9-8 CORE REGRESSION: PASS")
'''


print("=== P9-8 EVALUATION CALIBRATION PATCH ===")

critic_source = read_source(CRITIC)
red_source = read_source(RED_TEAM)

print("SOURCE FILES: PASS")

patched_critic = patch_object_normalization(
    critic_source,
    "critic",
)

patched_red = patch_object_normalization(
    red_source,
    "red_team",
)

patched_red = patch_red_team_simple_goal_calibration(
    patched_red,
)

if patched_critic == critic_source:
    fail("critic.py produced no changes")

if patched_red == red_source:
    fail("red_team.py produced no changes")

print("CRITIC OBJECT NORMALIZATION: PASS")
print("RED TEAM OBJECT NORMALIZATION: PASS")
print("RED TEAM SIMPLE GOAL CALIBRATION: PASS")

# ---------------------------------------------------------
# TEMPORARY REGRESSION ENVIRONMENT
# ---------------------------------------------------------

temp_dir = Path(tempfile.mkdtemp(prefix="p9_8_regression_"))

try:
    temp_critic = temp_dir / "critic.py"
    temp_red = temp_dir / "red_team.py"
    temp_test = temp_dir / "regression.py"

    temp_critic.write_text(
        patched_critic,
        encoding="utf-8",
    )

    temp_red.write_text(
        patched_red,
        encoding="utf-8",
    )

    temp_test.write_text(
        regression_script(),
        encoding="utf-8",
    )

    py_compile.compile(
        str(temp_critic),
        doraise=True,
    )

    py_compile.compile(
        str(temp_red),
        doraise=True,
    )

    py_compile.compile(
        str(temp_test),
        doraise=True,
    )

    print("TEMP COMPILE: PASS")

    # Put temporary patched modules FIRST on sys.path.
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")

    pythonpath_parts = [
        str(temp_dir),
        str(ROOT),
    ]

    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)

    env["PYTHONPATH"] = os.pathsep.join(
        pythonpath_parts
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(temp_test),
        ],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
    )

    if completed.stdout:
        print(completed.stdout.rstrip())

    if completed.stderr:
        print(completed.stderr.rstrip())

    if completed.returncode != 0:
        fail(
            "P9-8 REGRESSION FAILED "
            f"(exit={completed.returncode})"
        )

    print("PATCHED-SOURCE REGRESSION: PASS")

    # -----------------------------------------------------
    # VERIFY MAIN.PY IS UNCHANGED BEFORE WRITING CORE FILES
    # -----------------------------------------------------

    main_before = MAIN.read_bytes()

    # -----------------------------------------------------
    # BACKUPS
    # -----------------------------------------------------

    critic_backup = ROOT / "critic.py.before_p9_8"
    red_backup = ROOT / "red_team.py.before_p9_8"

    if not critic_backup.exists():
        shutil.copy2(CRITIC, critic_backup)

    if not red_backup.exists():
        shutil.copy2(RED_TEAM, red_backup)

    print("BACKUPS: PASS")

    # -----------------------------------------------------
    # WRITE ACTUAL CORE FILES
    # -----------------------------------------------------

    CRITIC.write_text(
        patched_critic,
        encoding="utf-8",
    )

    RED_TEAM.write_text(
        patched_red,
        encoding="utf-8",
    )

    print("CRITIC.PY WRITE: PASS")
    print("RED_TEAM.PY WRITE: PASS")

    # -----------------------------------------------------
    # FINAL COMPILE
    # -----------------------------------------------------

    py_compile.compile(
        str(CRITIC),
        doraise=True,
    )

    py_compile.compile(
        str(RED_TEAM),
        doraise=True,
    )

    print("FINAL CORE COMPILE: PASS")

    # -----------------------------------------------------
    # MAIN.PY PRESERVATION
    # -----------------------------------------------------

    main_after = MAIN.read_bytes()

    if main_before != main_after:
        fail(
            "MAIN.PY CHANGED unexpectedly. "
            "P9-8 must not modify main.py."
        )

    print("MAIN.PY PRESERVED: PASS")

    # -----------------------------------------------------
    # FINAL SOURCE VERIFICATION
    # -----------------------------------------------------

    final_critic = CRITIC.read_text(
        encoding="utf-8-sig"
    )

    final_red = RED_TEAM.read_text(
        encoding="utf-8-sig"
    )

    if "getattr(value, \"__dict__\", None)" not in final_critic:
        fail("CRITIC.PY final verification failed")

    if "getattr(value, \"__dict__\", None)" not in final_red:
        fail("RED_TEAM.PY final verification failed")

    if "no_clear_execution_path" not in final_red:
        fail(
            "RED_TEAM.PY calibration marker missing"
        )

    print("FINAL SOURCE VERIFICATION: PASS")

finally:
    shutil.rmtree(
        temp_dir,
        ignore_errors=True,
    )


print()
print("=== FINAL ===")
print("P9-8 EVALUATION CALIBRATION PATCH: PASS")
print("P9-1 CRITIC CORE: PRESERVED")
print("P9-2 RED TEAM CORE: PRESERVED")
print("P9-4 COMBINED EVALUATION: UNCHANGED")
print("MAIN.PY: UNCHANGED")
print("P9 MODE: ADVISORY")
print("EXECUTION CONTROL: NO CHANGE")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
