from pathlib import Path
import py_compile
import importlib
import shutil
import sys

APP_DIR = Path(__file__).resolve().parent
MAIN = APP_DIR / "main.py"
PLANNER = APP_DIR / "task_planner.py"
BACKUP = APP_DIR / "main.py.before_p7_2_task_planner"
TEMP = APP_DIR / "main.py.p7_2_test"

print("=== P7-2 TASK PLANNER -> MAIN v2.3 ===")

# ============================================================
# BASIC CHECKS
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
# PRECOMPILE
# ============================================================

try:
    py_compile.compile(str(MAIN), doraise=True)
    print("MAIN_PRECOMPILE: PASS")
except Exception as exc:
    print("MAIN_PRECOMPILE: FAIL")
    print("ERROR:", exc)
    raise SystemExit(1)

try:
    py_compile.compile(str(PLANNER), doraise=True)
    print("TASK_PLANNER_COMPILE: PASS")
except Exception as exc:
    print("TASK_PLANNER_COMPILE: FAIL")
    print("ERROR:", exc)
    raise SystemExit(1)

# ============================================================
# READ MAIN
# ============================================================

original = MAIN.read_text(encoding="utf-8")

required = [
    "# P6_STATE_MANAGER_INIT",
    "# GOAL_MANAGER_V6_INIT",
    "# THINK_X_P32_INIT",
    "# GOAL_MANAGER_V6_UPDATE",
    "# THINK_X_P32_ANALYZE",
    "# GOAL_MANAGER_V6_RESULT",
    "# 6. RESPONSE GUARD",
    'def status(self) -> dict[str, Any]:',
    '"router_guard": (',
    "MINH = MinhMiniCore()",
]

for anchor in required:
    if anchor not in original:
        print("STRUCTURE_ANCHOR_FAIL:", anchor)
        raise SystemExit(1)

print("MINH_MINI_CORE_STRUCTURE: PASS")

# ============================================================
# DUPLICATE GUARD
# ============================================================

duplicate_markers = [
    "# P7_2_TASK_PLANNER_IMPORT",
    "# P7_2_TASK_PLANNER_INIT",
    "# P7_2_TASK_PLANNER_GOAL_SYNC",
    "# P7_2_TASK_PLANNER_RESULT_SYNC",
    "def _p7_2_goal_to_dict",
    "def _p7_2_sync_task_planner_goal",
    "def _p7_2_sync_task_planner_result",
]

duplicates = [
    marker
    for marker in duplicate_markers
    if marker in original
]

if duplicates:
    print("P7-2_DUPLICATE_GUARD: FAIL")
    print("Existing:", ", ".join(duplicates))
    print("No modification made.")
    raise SystemExit(1)

print("P7-2_DUPLICATE_GUARD: PASS")

# ============================================================
# BACKUP
# ============================================================

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)

if not BACKUP.exists():
    print("BACKUP_EXISTS: FAIL")
    raise SystemExit(1)

print("BACKUP_EXISTS: PASS")

modified = original

try:

    # ========================================================
    # 1. TASK PLANNER IMPORT
    # ========================================================

    import_anchor = """        # THINK_X_P32_INIT
"""

    import_block = """        # P7_2_TASK_PLANNER_IMPORT
        try:
            from task_planner import create_task_planner
        except Exception as exc:
            create_task_planner = None
            log("TASK PLANNER IMPORT ERROR: " + repr(exc))

"""

    if import_anchor not in modified:
        raise RuntimeError(
            "THINK_X_P32_INIT anchor not found"
        )

    modified = modified.replace(
        import_anchor,
        import_block + import_anchor,
        1,
    )

    print("TASK_PLANNER_IMPORT: PASS")

    # ========================================================
    # 2. TASK PLANNER INIT
    # ========================================================

    init_anchor = """        # THINK_X_P32_INIT
"""

    init_block = """        # P7_2_TASK_PLANNER_INIT
        try:
            if create_task_planner is not None:
                self.task_planner = create_task_planner()
            else:
                self.task_planner = None
        except Exception as exc:
            self.task_planner = None
            log("TASK PLANNER INIT ERROR: " + repr(exc))

"""

    modified = modified.replace(
        init_anchor,
        init_block + init_anchor,
        1,
    )

    print("TASK_PLANNER_INIT: PASS")

    # ========================================================
    # 3. STATUS
    # ========================================================

    status_anchor = """            "router_guard": (
"""

    status_block = """            "task_planner": (
                self.task_planner is not None
            ),
            "task_planner_valid": (
                self.task_planner.validate().get("valid", False)
                if self.task_planner is not None
                else False
            ),
"""

    if status_anchor not in modified:
        raise RuntimeError(
            "status router_guard anchor not found"
        )

    modified = modified.replace(
        status_anchor,
        status_block + status_anchor,
        1,
    )

    print("TASK_PLANNER_STATUS: PASS")

    # ========================================================
    # 4. HELPERS
    # ========================================================

    helper_anchor = """    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

"""

    helpers = r'''    # --------------------------------------------------------
    # P7-2 TASK PLANNER HELPERS
    # --------------------------------------------------------

    def _p7_2_goal_to_dict(self, goal):
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

    def _p7_2_sync_task_planner_goal(self):
        planner = getattr(
            self,
            "task_planner",
            None,
        )

        manager = getattr(
            self,
            "goal_manager",
            None,
        )

        if planner is None or manager is None:
            return

        try:
            getter = getattr(
                manager,
                "get_current",
                None,
            )

            if not callable(getter):
                return

            goal = getter()

            goal_data = self._p7_2_goal_to_dict(
                goal
            )

            if not isinstance(goal_data, dict):
                return

            planner.set_goal(goal_data)

            existing_tasks = planner.get_tasks()

            if existing_tasks:
                return

            steps = goal_data.get("steps")

            if not isinstance(steps, list):
                return

            clean_steps = [
                str(step).strip()
                for step in steps
                if str(step).strip()
            ]

            if clean_steps:
                planner.create_plan(
                    goal_data,
                    clean_steps,
                )

        except Exception as exc:
            log(
                "TASK PLANNER GOAL SYNC ERROR: "
                + repr(exc)
            )

    def _p7_2_sync_task_planner_result(
        self,
        execution_result,
        verification_result=None,
    ):
        planner = getattr(
            self,
            "task_planner",
            None,
        )

        if planner is None:
            return

        try:
            current_task = planner.get_current_task()

            if not isinstance(current_task, dict):
                return

            task_id = current_task.get("id")

            if not task_id:
                return

            # P4-5 verification is authoritative.
            if isinstance(verification_result, dict):

                verified = verification_result.get(
                    "verified"
                )

                verification_status = (
                    verification_result.get("status")
                )

                verification_success = (
                    verification_result.get("success")
                )

                if (
                    verified is True
                    and verification_success is True
                ):
                    planner.update_task_status(
                        task_id,
                        "completed",
                    )
                    return

                if (
                    verification_status == "fail"
                    and verification_success is False
                ):
                    planner.update_task_status(
                        task_id,
                        "failed",
                    )
                    return

                # Clarification is blocked,
                # not execution failure.
                if verification_status == "blocked":
                    return

            # Fallback only when verification
            # is unavailable.
            if isinstance(execution_result, dict):

                execution_success = (
                    execution_result.get("success")
                )

                if execution_success is True:
                    planner.update_task_status(
                        task_id,
                        "completed",
                    )

                elif execution_success is False:
                    planner.update_task_status(
                        task_id,
                        "failed",
                    )

        except Exception as exc:
            log(
                "TASK PLANNER RESULT SYNC ERROR: "
                + repr(exc)
            )

'''

    if helper_anchor not in modified:
        raise RuntimeError(
            "STATUS helper anchor not found"
        )

    modified = modified.replace(
        helper_anchor,
        helpers + helper_anchor,
        1,
    )

    print("TASK_PLANNER_HELPERS: PASS")

    # ========================================================
    # 5. GOAL SYNC
    # ========================================================

    goal_sync_anchor = """        # THINK_X_P32_ANALYZE
"""

    goal_sync_block = """        # P7_2_TASK_PLANNER_GOAL_SYNC
        try:
            self._p7_2_sync_task_planner_goal()
        except Exception as exc:
            log(
                "TASK PLANNER GOAL SYNC CALL ERROR: "
                + repr(exc)
            )

"""

    if goal_sync_anchor not in modified:
        raise RuntimeError(
            "THINK_X_P32_ANALYZE anchor not found"
        )

    modified = modified.replace(
        goal_sync_anchor,
        goal_sync_block + goal_sync_anchor,
        1,
    )

    print("TASK_PLANNER_GOAL_SYNC: PASS")

    # ========================================================
    # 6. RESULT SYNC
    # ========================================================

    result_anchor = """        # ----------------------------------------------------
        # 6. RESPONSE GUARD
        # ----------------------------------------------------
"""

    result_block = """        # P7_2_TASK_PLANNER_RESULT_SYNC
        try:
            self._p7_2_sync_task_planner_result(
                execution_result,
                self.last_execution_verification,
            )
        except Exception as exc:
            log(
                "TASK PLANNER RESULT SYNC CALL ERROR: "
                + repr(exc)
            )

"""

    if result_anchor not in modified:
        raise RuntimeError(
            "RESPONSE GUARD process anchor not found"
        )

    modified = modified.replace(
        result_anchor,
        result_block + result_anchor,
        1,
    )

    print("TASK_PLANNER_RESULT_SYNC: PASS")

    # ========================================================
    # 7. TEMP WRITE
    # ========================================================

    TEMP.write_text(
        modified,
        encoding="utf-8",
    )

    print("TEMP_WRITE: PASS")

    # ========================================================
    # 8. TEMP COMPILE
    # ========================================================

    try:
        py_compile.compile(
            str(TEMP),
            doraise=True,
        )

        print("TEMP_COMPILE: PASS")

    except Exception as exc:
        print("TEMP_COMPILE: FAIL")
        print("ERROR:", exc)

        try:
            TEMP.unlink()
        except Exception:
            pass

        print("MAIN.PY MODIFIED: NO")
        raise SystemExit(1)

    # ========================================================
    # 9. REPLACE MAIN
    # ========================================================

    MAIN.write_text(
        modified,
        encoding="utf-8",
    )

    print("MAIN.PY MODIFIED: YES")

    try:
        TEMP.unlink()
    except Exception:
        pass

    # ========================================================
    # 10. MAIN COMPILE
    # ========================================================

    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )

        print("MAIN_COMPILE: PASS")

    except Exception as exc:
        print("MAIN_COMPILE: FAIL")
        print("ERROR:", exc)

        shutil.copy2(
            BACKUP,
            MAIN,
        )

        print("ROLLBACK: PASS")
        raise SystemExit(1)

    # ========================================================
    # 11. IMPORT
    # ========================================================

    try:
        sys.path.insert(
            0,
            str(APP_DIR),
        )

        if "main" in sys.modules:
            del sys.modules["main"]

        module = importlib.import_module(
            "main"
        )

        print("MAIN_IMPORT: PASS")

        # IMPORTANT:
        # main.py already creates:
        # MINH = MinhMiniCore()
        #
        # Therefore MINH is an INSTANCE,
        # not a callable class.

        instance = getattr(
            module,
            "MINH",
            None,
        )

        if instance is None:
            raise RuntimeError(
                "main.MINH not found"
            )

        print("MINH_GLOBAL_INSTANCE: PASS")

        class_name = type(instance).__name__

        if class_name != "MinhMiniCore":
            raise RuntimeError(
                "Unexpected MINH type: "
                + class_name
            )

        print("MINH_TYPE: PASS")

        planner = getattr(
            instance,
            "task_planner",
            None,
        )

        if planner is None:
            raise RuntimeError(
                "task_planner is None"
            )

        print("TASK_PLANNER_INSTANCE: PASS")

        status = instance.status()

        if not isinstance(status, dict):
            raise RuntimeError(
                "status() did not return dict"
            )

        if status.get("task_planner") is not True:
            raise RuntimeError(
                "status.task_planner != True"
            )

        print("TASK_PLANNER_STATUS: PASS")

        if status.get(
            "task_planner_valid"
        ) is not True:
            raise RuntimeError(
                "status.task_planner_valid != True"
            )

        print(
            "TASK_PLANNER_STATUS_VALID: PASS"
        )

    except Exception as exc:
        print(
            "MAIN_IMPORT_OR_RUNTIME: FAIL"
        )
        print("ERROR:", repr(exc))

        shutil.copy2(
            BACKUP,
            MAIN,
        )

        print("ROLLBACK: PASS")
        raise SystemExit(1)

    # ========================================================
    # FINAL
    # ========================================================

    print("")
    print("=== FINAL ===")
    print("P7-2 TASK PLANNER -> MAIN: PASS")
    print("P7-1 TASK PLANNER CORE: PRESERVED")
    print("P6-3 STATE MANAGER: PRESERVED")
    print("P5 WORLD MODEL: PRESERVED")
    print("P4-5 EXECUTE -> VERIFY: PRESERVED")
    print("AUTO EXECUTION: NO")
    print("AUTO GIT COMMIT: NO")

except SystemExit:
    raise

except Exception as exc:
    print("PATCH_ERROR:", repr(exc))

    try:
        if BACKUP.exists():
            shutil.copy2(
                BACKUP,
                MAIN,
            )
            print("ROLLBACK: PASS")
    except Exception as rollback_exc:
        print(
            "ROLLBACK: FAIL"
        )
        print(
            "ROLLBACK_ERROR:",
            repr(rollback_exc),
        )

    try:
        if TEMP.exists():
            TEMP.unlink()
    except Exception:
        pass

    raise SystemExit(1)
