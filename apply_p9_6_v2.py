from pathlib import Path
import py_compile
import shutil
import sys
import tempfile


APP_DIR = Path(__file__).resolve().parent
MAIN = APP_DIR / "main.py"
BACKUP = APP_DIR / "main.py.before_p9_6_p9_evaluation"


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


print("=== P9-6 P9 -> MAIN INTEGRATION V2 ===")

# ============================================================
# 1. FILE CHECK
# ============================================================

required_files = [
    "critic.py",
    "red_team.py",
    "fact_check.py",
    "combined_evaluation.py",
]

for filename in required_files:
    path = APP_DIR / filename

    if not path.exists():
        fail(f"missing required file: {filename}")

    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
    except Exception as exc:
        fail(f"{filename} compile failed: {exc}")

print("P9 CORE FILES: PASS")


# ============================================================
# 2. MAIN PRECOMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
except Exception as exc:
    fail(f"main.py precompile failed: {exc}")

print("MAIN PRECOMPILE: PASS")


source = MAIN.read_text(
    encoding="utf-8",
)


# ============================================================
# 3. DUPLICATE GUARD
# ============================================================

duplicate_markers = [
    "# P9_6_P9_EVALUATION_INIT",
    "# P9_6_P9_EVALUATION_HELPERS",
    "# P9_6_P9_EVALUATION_RUN",
    "self.p9_combined_evaluation",
]

for marker in duplicate_markers:
    if marker in source:
        fail(
            f"P9-6 already integrated: {marker}"
        )

print("DUPLICATE GUARD: PASS")


# ============================================================
# 4. IMPORTS
# ============================================================

imports = [
    "from critic import create_critic",
    "from red_team import create_red_team",
    "from fact_check import create_fact_check",
    "from combined_evaluation import create_combined_evaluation",
]

missing_imports = [
    line
    for line in imports
    if line not in source
]

if missing_imports:
    lines = source.splitlines(keepends=True)

    insert_index = None

    # Insert after the existing import section.
    last_import_index = None

    for index, line in enumerate(lines):
        stripped = line.strip()

        if (
            stripped.startswith("import ")
            or stripped.startswith("from ")
        ):
            last_import_index = index

        elif (
            last_import_index is not None
            and stripped
            and not stripped.startswith("#")
        ):
            break

    if last_import_index is None:
        fail("could not locate import section")

    insert_index = last_import_index + 1

    lines[insert_index:insert_index] = [
        line + "\n"
        for line in missing_imports
    ]

    source = "".join(lines)

print("P9 IMPORTS: PASS")


# ============================================================
# 5. INIT
# ============================================================

init_anchor = "# THINK_X_P32_INIT"

if source.count(init_anchor) != 1:
    fail(
        f"expected exactly one {init_anchor}, "
        f"found {source.count(init_anchor)}"
    )

init_block = '''
        # P9_6_P9_EVALUATION_INIT
        try:
            self.p9_critic = create_critic()
        except Exception as exc:
            self.p9_critic = None
            log(
                "P9 CRITIC INIT ERROR: "
                + repr(exc)
            )

        try:
            self.p9_red_team = create_red_team()
        except Exception as exc:
            self.p9_red_team = None
            log(
                "P9 RED TEAM INIT ERROR: "
                + repr(exc)
            )

        try:
            self.p9_fact_check = create_fact_check()
        except Exception as exc:
            self.p9_fact_check = None
            log(
                "P9 FACTCHECK INIT ERROR: "
                + repr(exc)
            )

        try:
            self.p9_combined_evaluation = (
                create_combined_evaluation()
            )
        except Exception as exc:
            self.p9_combined_evaluation = None
            log(
                "P9 COMBINED EVALUATION INIT ERROR: "
                + repr(exc)
            )

        self.last_p9_evaluation = None

'''

source = source.replace(
    init_anchor,
    init_block + "        " + init_anchor,
    1,
)

print("P9 INSTANCES: PASS")


# ============================================================
# 6. HELPERS
# ============================================================

status_anchor = "    # STATUS"

if source.count(status_anchor) != 1:
    fail(
        f"expected exactly one STATUS anchor, "
        f"found {source.count(status_anchor)}"
    )

helper_block = '''
    # P9_6_P9_EVALUATION_HELPERS
    def _p9_6_run_evaluation(
        self,
        goal=None,
        plan=None,
        result=None,
    ):
        """
        P9 advisory evaluation layer.

        This layer only evaluates supplied runtime data.

        It does NOT:
        - execute actions
        - route commands
        - call Web
        - call Ollama
        - mutate World Model
        - mutate State Manager execution state
        """

        try:
            critic_result = None
            red_team_result = None
            fact_check_result = None

            if self.p9_critic is not None:
                critic_result = self.p9_critic.evaluate(
                    goal=goal,
                    plan=plan,
                    result=result,
                )

            if self.p9_red_team is not None:
                red_team_result = self.p9_red_team.evaluate(
                    goal=goal,
                    plan=plan,
                    result=result,
                )

            if self.p9_fact_check is not None:
                facts = {}
                claims = []

                if isinstance(result, dict):
                    facts = {
                        "execution_success": result.get(
                            "success"
                        ),
                        "execution_status": result.get(
                            "status"
                        ),
                        "answer_present": result.get(
                            "answer_present"
                        ),
                    }

                    if result.get("success") is True:
                        claims.append(
                            {
                                "text": (
                                    "Execution result "
                                    "reports success."
                                ),
                                "supported": True,
                                "source": "runtime_result",
                            }
                        )

                    elif result.get("success") is False:
                        claims.append(
                            {
                                "text": (
                                    "Execution result "
                                    "reports failure."
                                ),
                                "supported": True,
                                "source": "runtime_result",
                            }
                        )

                fact_check_result = (
                    self.p9_fact_check.evaluate(
                        facts=facts,
                        claims=claims,
                    )
                )

            combined = None

            if self.p9_combined_evaluation is not None:
                combined = (
                    self.p9_combined_evaluation.evaluate(
                        critic_result=critic_result,
                        red_team_result=red_team_result,
                        fact_check_result=fact_check_result,
                    )
                )

            self.last_p9_evaluation = {
                "critic": critic_result,
                "red_team": red_team_result,
                "fact_check": fact_check_result,
                "combined": combined,
            }

            return self.last_p9_evaluation

        except Exception as exc:
            self.last_p9_evaluation = {
                "critic": None,
                "red_team": None,
                "fact_check": None,
                "combined": {
                    "verdict": "review",
                    "valid": False,
                    "score": 0.0,
                    "issues": [
                        {
                            "source": "p9_runtime",
                            "item": (
                                f"{type(exc).__name__}: "
                                f"{exc}"
                            ),
                        }
                    ],
                    "warnings": [],
                    "reason": (
                        "P9 evaluation failed safely."
                    ),
                },
            }

            return self.last_p9_evaluation

    def _p9_6_get_evaluation_status(self):
        evaluation = getattr(
            self,
            "last_p9_evaluation",
            None,
        )

        if not isinstance(evaluation, dict):
            return {
                "available": False,
                "verdict": None,
                "valid": False,
            }

        combined = evaluation.get(
            "combined"
        )

        if not isinstance(combined, dict):
            return {
                "available": False,
                "verdict": None,
                "valid": False,
            }

        return {
            "available": True,
            "verdict": combined.get(
                "verdict"
            ),
            "valid": combined.get(
                "valid"
            ),
            "score": combined.get(
                "score"
            ),
        }

'''

source = source.replace(
    status_anchor,
    helper_block + status_anchor,
    1,
)

print("P9 HELPERS: PASS")


# ============================================================
# 7. EXACT RUNTIME ANCHOR
# ============================================================

sync_start = (
    "        # P7_2_TASK_PLANNER_RESULT_SYNC"
)

sync_end = (
    "        # ----------------------------------------------------\n"
    "        # 6. RESPONSE GUARD"
)

if source.count(sync_start) != 1:
    fail(
        "P7 task planner sync anchor "
        "is not unique"
    )

if source.count(sync_end) != 1:
    fail(
        "response guard anchor "
        "is not unique"
    )

start_pos = source.find(sync_start)
end_pos = source.find(
    sync_end,
    start_pos,
)

if end_pos == -1:
    fail(
        "response guard does not occur "
        "after P7 result sync"
    )

if end_pos <= start_pos:
    fail(
        "invalid P7 -> response ordering"
    )


# ============================================================
# 8. P9 RUNTIME BLOCK
# ============================================================

evaluation_block = '''
        # P9_6_P9_EVALUATION_RUN
        # Advisory only.
        # Must not modify execution control.
        try:
            p9_goal = None
            p9_plan = None

            if self.goal_manager is not None:
                try:
                    get_current = getattr(
                        self.goal_manager,
                        "get_current",
                        None,
                    )

                    if callable(get_current):
                        p9_goal = get_current()

                except Exception as exc:
                    log(
                        "P9 GOAL READ ERROR: "
                        + repr(exc)
                    )

            if self.task_planner is not None:
                try:
                    get_plan = getattr(
                        self.task_planner,
                        "get_plan",
                        None,
                    )

                    if callable(get_plan):
                        p9_plan = get_plan()

                except Exception as exc:
                    log(
                        "P9 PLAN READ ERROR: "
                        + repr(exc)
                    )

            p9_result = None

            if isinstance(
                execution_result,
                dict,
            ):
                p9_result = dict(
                    execution_result
                )

            elif hasattr(
                execution_result,
                "__dict__",
            ):
                p9_result = dict(
                    execution_result.__dict__
                )

            else:
                p9_result = execution_result

            if isinstance(
                p9_result,
                dict,
            ):
                if isinstance(
                    self.last_execution_verification,
                    dict,
                ):
                    p9_result["verification"] = dict(
                        self.last_execution_verification
                    )

                p9_result["answer_present"] = bool(
                    answer
                )

            self._p9_6_run_evaluation(
                goal=p9_goal,
                plan=p9_plan,
                result=p9_result,
            )

        except Exception as exc:
            log(
                "P9 EVALUATION RUN ERROR: "
                + repr(exc)
            )

'''

source = (
    source[:end_pos]
    + evaluation_block
    + source[end_pos:]
)

print("P9 EVALUATION CALL: PASS")


# ============================================================
# 9. STATIC ORDER CHECK
# ============================================================

final_source = source

positions = {
    "P4_VERIFY": final_source.find(
        "# P45_EXECUTION_VERIFY"
    ),
    "P6_STATE": final_source.find(
        "# P6_STATE_MANAGER_EXECUTION_RESULT"
    ),
    "P5_WORLD": final_source.find(
        "# P5_WORLD_MODEL_OBSERVATION"
    ),
    "P7_RESULT": final_source.find(
        "# P7_2_TASK_PLANNER_RESULT_SYNC"
    ),
    "P9_RUN": final_source.find(
        "# P9_6_P9_EVALUATION_RUN"
    ),
    "RESPONSE_GUARD": final_source.find(
        "# 6. RESPONSE GUARD"
    ),
}

for name, position in positions.items():
    if position == -1:
        fail(
            f"missing final order marker: {name}"
        )

if not (
    positions["P4_VERIFY"]
    < positions["P6_STATE"]
    < positions["P5_WORLD"]
    < positions["P7_RESULT"]
    < positions["P9_RUN"]
    < positions["RESPONSE_GUARD"]
):
    fail(
        "P9 execution order is invalid"
    )

print("P4-5 -> P6 -> P5 -> P7 -> P9 -> RESPONSE: PASS")


# ============================================================
# 10. SAFETY CHECK
# ============================================================

for forbidden in [
    "self.execute_decision(",
    "subprocess.",
    "os.system(",
    "requests.",
    "urllib.request",
]:
    if forbidden in evaluation_block:
        fail(
            "P9 runtime block contains forbidden "
            f"execution/network operation: {forbidden}"
        )

print("P9 ADVISORY SAFETY: PASS")


# ============================================================
# 11. TEMP COMPILE
# ============================================================

temp_path = None

with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".py",
    prefix="main_p9_6_v2_",
    dir=str(APP_DIR),
    delete=False,
    encoding="utf-8",
) as temp_file:
    temp_path = Path(temp_file.name)
    temp_file.write(source)

try:
    py_compile.compile(
        str(temp_path),
        doraise=True,
    )
except Exception as exc:
    print("TEMP COMPILE: FAIL")
    print(exc)

    try:
        temp_path.unlink()
    except Exception:
        pass

    print("MAIN.PY WAS NOT MODIFIED")
    sys.exit(1)

try:
    temp_path.unlink()
except Exception:
    pass

print("TEMP COMPILE: PASS")


# ============================================================
# 12. BACKUP
# ============================================================

if not BACKUP.exists():
    shutil.copy2(
        MAIN,
        BACKUP,
    )
    print(
        f"BACKUP CREATED: {BACKUP.name}"
    )
else:
    print(
        f"BACKUP EXISTS: {BACKUP.name}"
    )


# ============================================================
# 13. WRITE MAIN
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("MAIN.PY WRITE: PASS")


# ============================================================
# 14. FINAL COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
except Exception as exc:
    print("MAIN FINAL COMPILE: FAIL")
    print(exc)

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    try:
        py_compile.compile(
            str(MAIN),
            doraise=True,
        )

        print("ROLLBACK COMPILE: PASS")

    except Exception as rollback_exc:
        print(
            "ROLLBACK COMPILE: FAIL"
        )
        print(rollback_exc)

    sys.exit(1)

print("MAIN FINAL COMPILE: PASS")


# ============================================================
# 15. FINAL MARKER CHECK
# ============================================================

final_source = MAIN.read_text(
    encoding="utf-8",
)

required_markers = [
    "# P9_6_P9_EVALUATION_INIT",
    "# P9_6_P9_EVALUATION_HELPERS",
    "# P9_6_P9_EVALUATION_RUN",
    "self.p9_critic",
    "self.p9_red_team",
    "self.p9_fact_check",
    "self.p9_combined_evaluation",
    "self.last_p9_evaluation",
]

for marker in required_markers:
    if marker not in final_source:
        print(
            f"FINAL MARKER FAIL: {marker}"
        )

        shutil.copy2(
            BACKUP,
            MAIN,
        )

        print("ROLLBACK: PASS")
        sys.exit(1)

print("P9-6 MARKERS: PASS")


# ============================================================
# 16. FINAL IMPORT
# ============================================================

try:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "main_p9_6_validation",
        str(MAIN),
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "could not create import spec"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    if not hasattr(module, "MINH"):
        raise RuntimeError(
            "global MINH instance missing"
        )

except Exception as exc:
    print("FINAL IMPORT: FAIL")
    print(exc)

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)

print("FINAL IMPORT: PASS")
print("GLOBAL MINH: PASS")


# ============================================================
# FINAL
# ============================================================

print("\n=== FINAL ===")
print("P9-6 P9 -> MAIN: PASS")
print("P9-1 CRITIC CORE: PRESERVED")
print("P9-2 RED TEAM CORE: PRESERVED")
print("P9-3 FACTCHECK CORE: PRESERVED")
print("P9-4 COMBINED EVALUATION CORE: PRESERVED")
print("P8-2 BE CRITIC: PRESERVED")
print("P7-2 TASK PLANNER: PRESERVED")
print("P6-3 STATE MANAGER: PRESERVED")
print("P5 WORLD MODEL: PRESERVED")
print("P4-5 EXECUTE -> VERIFY: PRESERVED")
print("P9 MODE: ADVISORY")
print("P9 EXECUTION CONTROL: NO")
print("AUTO EXECUTION: NO")
print("AUTO GIT COMMIT: NO")
print(f"BACKUP: {BACKUP.name}")
