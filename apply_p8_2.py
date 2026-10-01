from pathlib import Path
import py_compile
import shutil
import importlib.util
import sys


BASE = Path(__file__).resolve().parent

MAIN_FILE = BASE / "main.py"
BE_CRITIC_FILE = BASE / "be_critic.py"
BACKUP_FILE = BASE / "main.py.before_p8_2_be_critic"
TEMP_FILE = BASE / "main_p8_2_temp.py"


def fail(message):
    raise RuntimeError(message)


def require_exact(text, needle, label):
    count = text.count(needle)

    if count != 1:
        fail(
            f"{label}: expected exactly 1 occurrence, found {count}"
        )


def compile_file(path, label):
    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )

        print(f"{label}: PASS")

    except Exception as exc:
        fail(
            f"{label}: FAIL ({exc})"
        )


def import_module_from_path(path, module_name):
    spec = importlib.util.spec_from_file_location(
        module_name,
        str(path),
    )

    if spec is None or spec.loader is None:
        fail(
            f"{module_name}: import spec unavailable"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    old_main = sys.modules.get("main")

    try:
        sys.modules["main"] = module
        spec.loader.exec_module(module)

    finally:
        if old_main is not None:
            sys.modules["main"] = old_main
        else:
            sys.modules.pop("main", None)

    return module


print("=== P8-2 BE CRITIC -> MAIN ===")


# ============================================================
# FILE CHECK
# ============================================================

if not MAIN_FILE.exists():
    fail("MAIN_FILE: missing main.py")

if not BE_CRITIC_FILE.exists():
    fail("BE_CRITIC_FILE: missing be_critic.py")

print("MAIN_FILE: PASS")
print("BE_CRITIC_FILE: PASS")


# ============================================================
# PRECOMPILE
# ============================================================

compile_file(
    MAIN_FILE,
    "MAIN_PRECOMPILE",
)

compile_file(
    BE_CRITIC_FILE,
    "BE_CRITIC_COMPILE",
)


main_text = MAIN_FILE.read_text(
    encoding="utf-8-sig"
)

critic_text = BE_CRITIC_FILE.read_text(
    encoding="utf-8-sig"
)


# ============================================================
# EXISTING STRUCTURE
# ============================================================

require_exact(
    main_text,
    "class MinhMiniCore:",
    "MINH_MINI_CORE",
)

require_exact(
    main_text,
    "# P7_2_TASK_PLANNER_IMPORT",
    "TASK_PLANNER_IMPORT",
)

require_exact(
    main_text,
    "# P7_2_TASK_PLANNER_INIT",
    "TASK_PLANNER_INIT",
)

require_exact(
    main_text,
    "def _p7_2_goal_to_dict(self, goal):",
    "TASK_PLANNER_GOAL_HELPER",
)

require_exact(
    main_text,
    "def _p7_2_sync_task_planner_goal(self):",
    "TASK_PLANNER_GOAL_SYNC_HELPER",
)

require_exact(
    main_text,
    "def _p7_2_sync_task_planner_result(",
    "TASK_PLANNER_RESULT_SYNC_HELPER",
)

require_exact(
    main_text,
    "# P7_2_TASK_PLANNER_GOAL_SYNC",
    "TASK_PLANNER_GOAL_SYNC_MARKER",
)

require_exact(
    main_text,
    "# P7_2_TASK_PLANNER_RESULT_SYNC",
    "TASK_PLANNER_RESULT_SYNC_MARKER",
)

require_exact(
    main_text,
    "# THINK_X_P32_INIT",
    "THINK_X_INIT",
)

require_exact(
    main_text,
    '"router_guard": (',
    "STATUS_ROUTER_GUARD",
)

require_exact(
    main_text,
    "MINH = MinhMiniCore()",
    "GLOBAL_MINH",
)


# ============================================================
# BE CRITIC API
# ============================================================

require_exact(
    critic_text,
    "class BECritic:",
    "BE_CRITIC_CLASS",
)

require_exact(
    critic_text,
    "    def evaluate(",
    "BE_CRITIC_EVALUATE",
)

require_exact(
    critic_text,
    "    def get_last_result(",
    "BE_CRITIC_LAST_RESULT",
)

require_exact(
    critic_text,
    "    def validate(",
    "BE_CRITIC_VALIDATE",
)

print("EXISTING_STRUCTURE: PASS")
print("BE_CRITIC_API: PASS")


# ============================================================
# DUPLICATE GUARD
# ============================================================

duplicate_markers = [
    "# P8_2_BE_CRITIC_IMPORT",
    "# P8_2_BE_CRITIC_INIT",
    "def _p8_2_goal_to_dict(self, goal):",
    "def _p8_2_get_critic_goal(self):",
    "def _p8_2_get_critic_plan(self):",
    "def _p8_2_evaluate_be_critic(self):",
    "# P8_2_BE_CRITIC_EVALUATE",
]

for marker in duplicate_markers:

    if marker in main_text:
        fail(
            "P8_2_DUPLICATE_GUARD: "
            + marker
        )

print("P8_2_DUPLICATE_GUARD: PASS")


# ============================================================
# BUILD PATCH
# ============================================================

new_text = main_text


# ============================================================
# 1. IMPORT + INIT
# ============================================================

think_init_anchor = "        # THINK_X_P32_INIT"

require_exact(
    new_text,
    think_init_anchor,
    "THINK_X_INIT_ANCHOR",
)

critic_init_block = '''        # P8_2_BE_CRITIC_IMPORT
        try:
            from be_critic import create_be_critic
        except Exception as exc:
            create_be_critic = None
            log(
                "BE CRITIC IMPORT ERROR: "
                + repr(exc)
            )

        # P8_2_BE_CRITIC_INIT
        try:
            if create_be_critic is not None:
                self.be_critic = create_be_critic()
            else:
                self.be_critic = None
        except Exception as exc:
            self.be_critic = None
            log(
                "BE CRITIC INIT ERROR: "
                + repr(exc)
            )

'''

new_text = new_text.replace(
    think_init_anchor,
    critic_init_block + think_init_anchor,
    1,
)


# ============================================================
# 2. HELPERS
# ============================================================

p7_helpers_anchor = (
    "    # --------------------------------------------------------\n"
    "    # P7-2 TASK PLANNER HELPERS"
)

require_exact(
    new_text,
    p7_helpers_anchor,
    "P7_HELPERS_ANCHOR",
)

critic_helpers = '''    # --------------------------------------------------------
    # P8-2 BE CRITIC HELPERS
    # --------------------------------------------------------

    def _p8_2_goal_to_dict(self, goal):
        if goal is None:
            return None

        try:
            converter = getattr(
                goal,
                "to_dict",
                None,
            )

            if callable(converter):
                value = converter()

                if isinstance(value, dict):
                    return dict(value)

        except Exception:
            pass

        if isinstance(goal, dict):
            return dict(goal)

        try:
            value = getattr(
                goal,
                "__dict__",
                None,
            )

            if isinstance(value, dict):
                return dict(value)

        except Exception:
            pass

        return None

    def _p8_2_get_critic_goal(self):
        manager = getattr(
            self,
            "goal_manager",
            None,
        )

        if manager is None:
            return None

        try:
            getter = getattr(
                manager,
                "get_current",
                None,
            )

            if not callable(getter):
                return None

            goal = getter()

            return self._p8_2_goal_to_dict(
                goal
            )

        except Exception as exc:
            log(
                "BE CRITIC GOAL ERROR: "
                + repr(exc)
            )

            return None

    def _p8_2_get_critic_plan(self):
        planner = getattr(
            self,
            "task_planner",
            None,
        )

        if planner is None:
            return None

        try:
            getter = getattr(
                planner,
                "get_plan",
                None,
            )

            if not callable(getter):
                return None

            value = getter()

            if isinstance(value, dict):
                return dict(value)

            return value

        except Exception as exc:
            log(
                "BE CRITIC PLAN ERROR: "
                + repr(exc)
            )

            return None

    def _p8_2_evaluate_be_critic(self):
        critic = getattr(
            self,
            "be_critic",
            None,
        )

        if critic is None:
            return None

        goal = self._p8_2_get_critic_goal()
        plan = self._p8_2_get_critic_plan()

        try:
            result = critic.evaluate(
                goal,
                plan,
            )

            if isinstance(result, dict):
                return dict(result)

        except Exception as exc:
            log(
                "BE CRITIC EVALUATE ERROR: "
                + repr(exc)
            )

        return None

'''

new_text = new_text.replace(
    p7_helpers_anchor,
    critic_helpers + p7_helpers_anchor,
    1,
)


# ============================================================
# 3. STATUS
# ============================================================

router_guard_anchor = '            "router_guard": ('

require_exact(
    new_text,
    router_guard_anchor,
    "ROUTER_GUARD_ANCHOR",
)

critic_status_block = '''            "be_critic": (
                self.be_critic is not None
            ),
            "be_critic_valid": (
                self.be_critic.validate().get(
                    "valid",
                    False,
                )
                if self.be_critic is not None
                else False
            ),
            "be_critic_last_verdict": (
                (
                    self.be_critic.get_last_result()
                    or {}
                ).get("verdict")
                if self.be_critic is not None
                else None
            ),
'''

new_text = new_text.replace(
    router_guard_anchor,
    critic_status_block + router_guard_anchor,
    1,
)


# ============================================================
# 4. INSERT EVALUATION
# Use ONLY the confirmed marker.
# ============================================================

goal_sync_marker = "        # P7_2_TASK_PLANNER_GOAL_SYNC"

require_exact(
    new_text,
    goal_sync_marker,
    "P7_2_GOAL_SYNC_MARKER_AFTER_PATCH",
)

critic_evaluate_block = '''        # P8_2_BE_CRITIC_EVALUATE
        # Advisory only.
        # P8-2 does NOT block routing or execution.

        be_critic_result = None

        try:
            be_critic_result = (
                self._p8_2_evaluate_be_critic()
            )
        except Exception as exc:
            log(
                "BE CRITIC EVALUATION ERROR: "
                + repr(exc)
            )

        if (
            isinstance(be_critic_result, dict)
            and self.state_manager is not None
        ):
            try:
                self.state_manager.update(
                    {
                        "be_critic": dict(
                            be_critic_result
                        )
                    }
                )
            except Exception as exc:
                log(
                    "BE CRITIC STATE ERROR: "
                    + repr(exc)
                )

'''

new_text = new_text.replace(
    goal_sync_marker,
    goal_sync_marker + "\n" + critic_evaluate_block.rstrip(),
    1,
)


# ============================================================
# 5. PRESERVATION
# ============================================================

preserved_markers = [
    "# P5_WORLD_MODEL_INIT",
    "# P6_STATE_MANAGER_INIT",
    "# P7_2_TASK_PLANNER_IMPORT",
    "# P7_2_TASK_PLANNER_INIT",
    "def _p7_2_sync_task_planner_goal(self):",
    "def _p7_2_sync_task_planner_result(",
    "# P7_2_TASK_PLANNER_RESULT_SYNC",
    "# P45_EXECUTION_VERIFY_INIT",
    "self.last_execution_verification = None",
]

for marker in preserved_markers:

    if marker not in new_text:
        fail(
            "PRESERVATION_CHECK failed: "
            + marker
        )

print(
    "P4_P5_P6_P7_PRESERVATION: PASS"
)


# ============================================================
# 6. TEMP FILE
# ============================================================

if TEMP_FILE.exists():
    TEMP_FILE.unlink()

TEMP_FILE.write_text(
    new_text,
    encoding="utf-8",
)

print(
    "TEMP_WRITE: PASS"
)

compile_file(
    TEMP_FILE,
    "TEMP_COMPILE",
)


# ============================================================
# 7. TEMP IMPORT
# ============================================================

try:

    temp_module = import_module_from_path(
        TEMP_FILE,
        "main_p8_2_temp",
    )

    print(
        "TEMP_IMPORT: PASS"
    )

except Exception as exc:

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    fail(
        "TEMP_IMPORT: FAIL "
        + repr(exc)
    )


# ============================================================
# 8. TEMP GLOBAL MINH
# ============================================================

temp_minh = getattr(
    temp_module,
    "MINH",
    None,
)

if temp_minh is None:

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    fail(
        "TEMP_GLOBAL_MINH: FAIL"
    )

print(
    "TEMP_GLOBAL_MINH: PASS"
)


# ============================================================
# 9. TEMP BE CRITIC
# ============================================================

temp_critic = getattr(
    temp_minh,
    "be_critic",
    None,
)

if temp_critic is None:

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    fail(
        "TEMP_BE_CRITIC_INSTANCE: FAIL"
    )

print(
    "TEMP_BE_CRITIC_INSTANCE: PASS"
)


try:

    validation = (
        temp_critic.validate()
    )

    if not isinstance(
        validation,
        dict,
    ):
        fail(
            "BE Critic validate() "
            "did not return dict"
        )

    if not validation.get(
        "valid",
        False,
    ):
        fail(
            "BE Critic validation failed: "
            + repr(validation)
        )

    print(
        "TEMP_BE_CRITIC_VALIDATE: PASS"
    )

except Exception as exc:

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    fail(
        "TEMP_BE_CRITIC_VALIDATE: FAIL "
        + repr(exc)
    )


# ============================================================
# 10. CHECK P8-2 MARKERS IN TEMP
# ============================================================

temp_markers = [
    "# P8_2_BE_CRITIC_IMPORT",
    "# P8_2_BE_CRITIC_INIT",
    "def _p8_2_goal_to_dict(self, goal):",
    "def _p8_2_get_critic_goal(self):",
    "def _p8_2_get_critic_plan(self):",
    "def _p8_2_evaluate_be_critic(self):",
    "# P8_2_BE_CRITIC_EVALUATE",
]

for marker in temp_markers:

    require_exact(
        new_text,
        marker,
        "TEMP_P8_2_MARKER",
    )

print(
    "TEMP_P8_2_MARKERS: PASS"
)


# ============================================================
# 11. BACKUP
# ============================================================

if BACKUP_FILE.exists():

    print(
        "BACKUP_EXISTS: existing backup preserved"
    )

else:

    shutil.copy2(
        MAIN_FILE,
        BACKUP_FILE,
    )

    print(
        "BACKUP_CREATED: PASS"
    )


# ============================================================
# 12. WRITE REAL MAIN
# ============================================================

try:

    MAIN_FILE.write_text(
        new_text,
        encoding="utf-8",
    )

    print(
        "MAIN_WRITE: PASS"
    )

except Exception as exc:

    if BACKUP_FILE.exists():
        shutil.copy2(
            BACKUP_FILE,
            MAIN_FILE,
        )

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    fail(
        "MAIN_WRITE: FAIL; "
        "backup restored: "
        + repr(exc)
    )


# ============================================================
# 13. FINAL REAL VALIDATION
# ============================================================

try:

    compile_file(
        MAIN_FILE,
        "MAIN_FINAL_COMPILE",
    )

    final_module = import_module_from_path(
        MAIN_FILE,
        "main_p8_2_final",
    )

    print(
        "MAIN_FINAL_IMPORT: PASS"
    )

    final_minh = getattr(
        final_module,
        "MINH",
        None,
    )

    if final_minh is None:
        raise RuntimeError(
            "global MINH missing"
        )

    print(
        "MAIN_FINAL_GLOBAL_MINH: PASS"
    )

    final_critic = getattr(
        final_minh,
        "be_critic",
        None,
    )

    if final_critic is None:
        raise RuntimeError(
            "be_critic instance missing"
        )

    print(
        "MAIN_FINAL_BE_CRITIC: PASS"
    )

    final_validation = (
        final_critic.validate()
    )

    if not isinstance(
        final_validation,
        dict,
    ):
        raise RuntimeError(
            "invalid BE Critic validation"
        )

    if not final_validation.get(
        "valid",
        False,
    ):
        raise RuntimeError(
            "BE Critic validation failed: "
            + repr(final_validation)
        )

    print(
        "MAIN_FINAL_BE_CRITIC_VALID: PASS"
    )

except Exception as exc:

    print(
        "FINAL_VALIDATION: FAIL",
        repr(exc),
    )

    if BACKUP_FILE.exists():

        shutil.copy2(
            BACKUP_FILE,
            MAIN_FILE,
        )

        print(
            "ROLLBACK_FROM_BACKUP: PASS"
        )

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    raise


# ============================================================
# CLEANUP
# ============================================================

if TEMP_FILE.exists():
    TEMP_FILE.unlink()


# ============================================================
# FINAL
# ============================================================

print("")
print("=== FINAL ===")
print("P8-2 BE CRITIC -> MAIN: PASS")
print("P8-1 BE CRITIC CORE: PRESERVED")
print("P7-2 TASK PLANNER: PRESERVED")
print("P6-3 STATE MANAGER: PRESERVED")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("BE CRITIC MODE: ADVISORY")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
print("BACKUP:", BACKUP_FILE.name)

