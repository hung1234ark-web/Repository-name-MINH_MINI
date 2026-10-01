from pathlib import Path
import py_compile
import shutil
import re
import sys
import tempfile


APP_DIR = Path(__file__).resolve().parent
MAIN = APP_DIR / "main.py"
BACKUP = APP_DIR / "main.py.before_p9_6_p9_evaluation"


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


if not MAIN.exists():
    fail("main.py not found")

source = MAIN.read_text(encoding="utf-8")

print("=== P9-6 P9 -> MAIN INTEGRATION ===")

# ============================================================
# 1. PRE-CHECK
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
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        fail(f"{filename} compile failed: {exc}")

print("P9 CORE FILES: PASS")

try:
    py_compile.compile(str(MAIN), doraise=True)
except Exception as exc:
    fail(f"main.py precompile failed: {exc}")

print("MAIN PRECOMPILE: PASS")


# ============================================================
# 2. DUPLICATE GUARD
# ============================================================

if "# P9_6_P9_EVALUATION_INIT" in source:
    fail("P9-6 already integrated")

if "# P9_6_P9_EVALUATION_HELPERS" in source:
    fail("P9-6 helper block already exists")

if "self.p9_combined_evaluation" in source:
    fail("P9 Combined Evaluation instance already exists")

print("DUPLICATE GUARD: PASS")


# ============================================================
# 3. IMPORT BLOCK
# ============================================================

import_patterns = [
    "from critic import create_critic",
    "from red_team import create_red_team",
    "from fact_check import create_fact_check",
    "from combined_evaluation import create_combined_evaluation",
]

missing_imports = [
    line for line in import_patterns
    if line not in source
]

# P9-1/P9-2/P9-3/P9-4 are standalone files.
# Add only imports that are not already present.

if missing_imports:
    import_block = "\n".join(
        f"from {line.split(' import ')[0].replace('from ', '')} import "
        f"{line.split(' import ')[1]}"
        for line in missing_imports
    )

    # Find a stable first import section.
    lines = source.splitlines(keepends=True)

    insert_at = None

    for index, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = index
            break

    if insert_at is None:
        fail("could not locate Python import section")

    lines.insert(
        insert_at,
        import_block + "\n",
    )

    source = "".join(lines)

print("P9 IMPORTS: PASS")


# ============================================================
# 4. INIT BLOCK
# ============================================================

init_block = r'''
        # P9_6_P9_EVALUATION_INIT
        try:
            self.p9_critic = create_critic()
        except Exception:
            self.p9_critic = None

        try:
            self.p9_red_team = create_red_team()
        except Exception:
            self.p9_red_team = None

        try:
            self.p9_fact_check = create_fact_check()
        except Exception:
            self.p9_fact_check = None

        try:
            self.p9_combined_evaluation = create_combined_evaluation()
        except Exception:
            self.p9_combined_evaluation = None

        self.last_p9_evaluation = None
'''

# Find existing BE Critic initialization.
be_init_pattern = re.compile(
    r'(?P<indent>^[ \t]*)# P8_2_BE_CRITIC_INIT.*?$',
    re.MULTILINE,
)

match = be_init_pattern.search(source)

if match:
    line_end = source.find("\n", match.end())

    if line_end == -1:
        line_end = len(source)

    insertion_point = line_end + 1

    source = (
        source[:insertion_point]
        + init_block
        + source[insertion_point:]
    )

else:
    # Fallback: place immediately before first status marker
    status_marker = source.find("# STATUS")

    if status_marker == -1:
        fail("could not locate safe initialization anchor")

    # Determine indentation from the class body.
    source = (
        source[:status_marker]
        + init_block
        + "\n"
        + source[status_marker:]
    )

print("P9 INSTANCES: PASS")


# ============================================================
# 5. HELPER METHODS
# ============================================================

helper_block = r'''
    # P9_6_P9_EVALUATION_HELPERS
    def _p9_6_run_evaluation(self, goal=None, plan=None, result=None):
        """
        P9-6 advisory evaluation layer.

        Critic + Red Team + FactCheck + Combined Evaluation
        only inspect runtime data.

        They do NOT:
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

                if isinstance(result, dict):
                    facts = {
                        "execution_success": result.get("success"),
                        "execution_status": result.get("status"),
                        "answer_present": result.get("answer_present"),
                    }

                claims = []

                if isinstance(result, dict):
                    if result.get("success") is True:
                        claims.append({
                            "text": "Execution result reports success.",
                            "supported": True,
                            "source": "runtime_result",
                        })
                    elif result.get("success") is False:
                        claims.append({
                            "text": "Execution result reports failure.",
                            "supported": True,
                            "source": "runtime_result",
                        })

                fact_check_result = self.p9_fact_check.evaluate(
                    facts=facts,
                    claims=claims,
                )

            if self.p9_combined_evaluation is not None:
                combined = self.p9_combined_evaluation.evaluate(
                    critic_result=critic_result,
                    red_team_result=red_team_result,
                    fact_check_result=fact_check_result,
                )
            else:
                combined = None

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
                            "item": f"{type(exc).__name__}: {exc}",
                        }
                    ],
                    "warnings": [],
                    "reason": "P9 evaluation failed safely.",
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

        combined = evaluation.get("combined")

        if not isinstance(combined, dict):
            return {
                "available": False,
                "verdict": None,
                "valid": False,
            }

        return {
            "available": True,
            "verdict": combined.get("verdict"),
            "valid": combined.get("valid"),
            "score": combined.get("score"),
        }
'''

# Safe anchor: helper area immediately before STATUS.
status_marker = source.find("# STATUS")

if status_marker == -1:
    fail("could not locate # STATUS marker for helper insertion")

source = (
    source[:status_marker]
    + helper_block
    + "\n"
    + source[status_marker:]
)

print("P9 HELPERS: PASS")


# ============================================================
# 6. EVALUATION CALL
# ============================================================

evaluation_call = r'''
        # P9_6_P9_EVALUATION_RUN
        try:
            p9_goal = None
            p9_plan = None

            if hasattr(self, "goal_manager"):
                try:
                    current_goal = self.goal_manager.get_current_goal()
                except Exception:
                    current_goal = None

                if current_goal is not None:
                    p9_goal = current_goal

            if hasattr(self, "task_planner"):
                try:
                    p9_plan = self.task_planner.get_plan()
                except Exception:
                    p9_plan = None

            p9_result = None

            if isinstance(execution_result, dict):
                p9_result = dict(execution_result)

                if isinstance(
                    getattr(self, "last_execution_verification", None),
                    dict,
                ):
                    p9_result["verification"] = dict(
                        self.last_execution_verification
                    )

            self._p9_6_run_evaluation(
                goal=p9_goal,
                plan=p9_plan,
                result=p9_result,
            )

        except Exception:
            self.last_p9_evaluation = None
'''

# Find the execution verification block.
# We deliberately place evaluation after verification,
# but before final response/result processing.

verification_anchor = source.find(
    "self.last_execution_verification"
)

if verification_anchor == -1:
    fail(
        "could not locate last_execution_verification "
        "for P9 evaluation placement"
    )

# Find the next response/result guard after verification.
candidate_markers = [
    "response_guard",
    "return answer",
    "return response",
    "return result",
]

insert_position = None

for marker in candidate_markers:
    position = source.find(
        marker,
        verification_anchor,
    )

    if position != -1:
        # Only use anchors reasonably close to verification.
        distance = position - verification_anchor

        if 0 < distance < 20000:
            line_start = source.rfind("\n", 0, position) + 1
            insert_position = line_start
            break

if insert_position is None:
    fail(
        "could not locate safe post-verification "
        "runtime insertion point"
    )

source = (
    source[:insert_position]
    + evaluation_call
    + "\n"
    + source[insert_position:]
)

print("P9 EVALUATION CALL: PASS")


# ============================================================
# 7. TEMPORARY COMPILE
# ============================================================

with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".py",
    prefix="main_p9_6_",
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
    try:
        temp_path.unlink()
    except Exception:
        pass

    print("TEMP COMPILE: FAIL")
    print(exc)
    print("MAIN.PY WAS NOT MODIFIED")
    sys.exit(1)

try:
    temp_path.unlink()
except Exception:
    pass

print("TEMP COMPILE: PASS")


# ============================================================
# 8. STATIC PRESERVATION CHECK
# ============================================================

preserved_markers = [
    "last_execution_verification",
    "world_model",
    "state_manager",
    "task_planner",
    "be_critic",
]

for marker in preserved_markers:
    if marker not in source:
        fail(
            f"preservation check failed: "
            f"{marker} missing"
        )

print("P4-5/P5/P6/P7/P8 STRUCTURE: PRESERVED")


# ============================================================
# 9. BACKUP
# ============================================================

if not BACKUP.exists():
    shutil.copy2(MAIN, BACKUP)
    print(f"BACKUP CREATED: {BACKUP.name}")
else:
    print(f"BACKUP EXISTS: {BACKUP.name}")


# ============================================================
# 10. WRITE MAIN
# ============================================================

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("MAIN.PY WRITE: PASS")


# ============================================================
# 11. FINAL COMPILE
# ============================================================

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
except Exception as exc:
    print("MAIN FINAL COMPILE: FAIL")
    print(exc)

    print("ROLLBACK: START")

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
            "ROLLBACK COMPILE: FAIL",
            rollback_exc,
        )

    sys.exit(1)

print("MAIN FINAL COMPILE: PASS")


# ============================================================
# 12. FINAL STATIC CHECKS
# ============================================================

final_source = MAIN.read_text(
    encoding="utf-8",
)

final_markers = [
    "# P9_6_P9_EVALUATION_INIT",
    "# P9_6_P9_EVALUATION_HELPERS",
    "# P9_6_P9_EVALUATION_RUN",
    "self.p9_critic",
    "self.p9_red_team",
    "self.p9_fact_check",
    "self.p9_combined_evaluation",
    "self.last_p9_evaluation",
]

for marker in final_markers:
    if marker not in final_source:
        print(
            f"FINAL MARKER: FAIL -> {marker}"
        )

        shutil.copy2(
            BACKUP,
            MAIN,
        )

        print("ROLLBACK: PASS")
        sys.exit(1)

print("P9-6 MARKERS: PASS")


# ============================================================
# 13. IMPORT CHECK
# ============================================================

try:
    import py_compile as _py_compile

    _py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    print("FINAL IMPORT PRECHECK: PASS")

except Exception as exc:
    print("FINAL IMPORT PRECHECK: FAIL")
    print(exc)

    shutil.copy2(
        BACKUP,
        MAIN,
    )

    print("ROLLBACK: PASS")
    sys.exit(1)


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
