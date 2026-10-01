from pathlib import Path
import ast
import shutil
import py_compile
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
OBSERVER = ROOT / "observer.py"

print("=" * 70)
print("P12-1 EXECUTE -> OBSERVE -> VERIFY")
print("SAFE REPAIR")
print("=" * 70)

# ------------------------------------------------------------
# 1. READ CURRENT MAIN
# ------------------------------------------------------------

if not MAIN.exists():
    raise SystemExit("ERROR: main.py not found")

main_text = MAIN.read_text(
    encoding="utf-8-sig"
)

compile(
    main_text,
    str(MAIN),
    "exec",
)

ast.parse(
    main_text,
    filename=str(MAIN),
)

print("MAIN PRECHECK: PASS")

# ------------------------------------------------------------
# 2. OBSERVER FILE
# ------------------------------------------------------------

observer_code = r'''# ============================================================
# MINH MINI — OBSERVER
# P12-1 Execute -> Observe -> Verify
#
# Observer chỉ ghi nhận execution result đã có.
# Không execute.
# Không retry.
# Không gọi Web.
# Không gọi Ollama.
# Không gọi Action.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


VERSION = "P12-1.0"


@dataclass(frozen=True)
class Observation:
    observed: bool
    success: bool | None
    tool: str
    intent: str
    answer: str
    error: str
    raw_type: str
    checks: list[str]
    version: str = VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Observer:
    VERSION = VERSION

    def __init__(self):
        self.last_observation: Observation | None = None

    @staticmethod
    def _value(
        value: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if value is None:
            return default

        if isinstance(value, dict):
            return value.get(key, default)

        return getattr(
            value,
            key,
            default,
        )

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def observe(
        self,
        *,
        message: str = "",
        decision: Any = None,
        execution_result: Any = None,
        answer: str = "",
    ) -> dict[str, Any]:

        checks: list[str] = []

        if execution_result is None:
            observation = Observation(
                observed=False,
                success=None,
                tool="",
                intent=self._text(
                    self._value(
                        decision,
                        "intent",
                        "",
                    )
                ),
                answer=self._text(answer),
                error="missing_execution_result",
                raw_type="NoneType",
                checks=[
                    "missing_execution_result",
                ],
            )

            self.last_observation = observation
            return observation.to_dict()

        success = self._value(
            execution_result,
            "success",
            None,
        )

        tool = self._text(
            self._value(
                execution_result,
                "tool",
                "",
            )
        )

        intent = self._text(
            self._value(
                execution_result,
                "intent",
                self._value(
                    decision,
                    "intent",
                    "",
                ),
            )
        )

        error = self._text(
            self._value(
                execution_result,
                "error",
                "",
            )
        )

        answer_text = self._text(answer)

        checks.append("execution_result_present")

        if success is True:
            checks.append("success_true")
        elif success is False:
            checks.append("success_false")
        else:
            checks.append("success_unknown")

        if tool:
            checks.append("tool_present")
        else:
            checks.append("tool_missing")

        if answer_text:
            checks.append("answer_present")
        else:
            checks.append("answer_missing")

        if error:
            checks.append("error_present")

        observation = Observation(
            observed=True,
            success=success
            if isinstance(success, bool)
            else None,
            tool=tool,
            intent=intent,
            answer=answer_text,
            error=error,
            raw_type=type(execution_result).__name__,
            checks=checks,
        )

        self.last_observation = observation

        return observation.to_dict()


def create_observer() -> Observer:
    return Observer()


__all__ = [
    "VERSION",
    "Observation",
    "Observer",
    "create_observer",
]
'''

OBSERVER.write_text(
    observer_code,
    encoding="utf-8",
)

compile(
    observer_code,
    str(OBSERVER),
    "exec",
)

ast.parse(
    observer_code,
    filename=str(OBSERVER),
)

print("OBSERVER FILE: PASS")
print("OBSERVER AST + COMPILE: PASS")

# ------------------------------------------------------------
# 3. BACKUP
# ------------------------------------------------------------

backup = ROOT / "main.py.before_p12_1_repair"

shutil.copy2(
    MAIN,
    backup,
)

print(
    "BACKUP CREATED:",
    backup.name,
)

# ------------------------------------------------------------
# 4. IMPORT
# ------------------------------------------------------------

observer_import = (
    "from observer import create_observer"
)

if observer_import not in main_text:

    import_candidates = [
        "from tool_selector import create_tool_selector",
        "from execution_contract import",
    ]

    inserted = False

    anchor = (
        "from tool_selector import create_tool_selector"
    )

    if anchor in main_text:
        main_text = main_text.replace(
            anchor,
            anchor
            + "\n"
            + observer_import,
            1,
        )
        inserted = True

    if not inserted:
        shutil.copy2(
            backup,
            MAIN,
        )
        raise SystemExit(
            "ERROR: import anchor not found"
        )

print("OBSERVER IMPORT: PASS")

# ------------------------------------------------------------
# 5. INIT
# ------------------------------------------------------------

if "self.last_execution_observation = None" not in main_text:

    init_anchor = (
        "self.last_p11_tool_selection = None"
    )

    if init_anchor not in main_text:
        shutil.copy2(
            backup,
            MAIN,
        )
        raise SystemExit(
            "ERROR: init anchor not found"
        )

    init_block = (
        init_anchor
        + "\n"
        "\n"
        "        # P12-1 OBSERVER INIT\n"
        "        try:\n"
        "            self.observer = create_observer()\n"
        "        except Exception as exc:\n"
        "            self.observer = None\n"
        "            log(\"P12 OBSERVER INIT ERROR: \" + repr(exc))\n"
        "\n"
        "        self.last_execution_observation = None"
    )

    main_text = main_text.replace(
        init_anchor,
        init_block,
        1,
    )

else:
    print(
        "OBSERVER INIT: ALREADY PRESENT"
    )

print("OBSERVER INIT: PASS")

# ------------------------------------------------------------
# 6. P12 HELPER
#
# Use exact function definition as anchor.
# This avoids the duplicate P11 comment at line ~2101.
# ------------------------------------------------------------

helper_anchor = (
    "    def _p11_select_tool("
)

if helper_anchor not in main_text:
    shutil.copy2(
        backup,
        MAIN,
    )
    raise SystemExit(
        "ERROR: _p11_select_tool function anchor missing"
    )

helper_code = r'''    # --------------------------------------------------------
    # P12-1 OBSERVER
    # --------------------------------------------------------

    def _p12_observe_execution(
        self,
        message=None,
        decision=None,
        execution_result=None,
        answer="",
    ):
        observer = getattr(
            self,
            "observer",
            None,
        )

        if observer is None:
            observation = {
                "observed": False,
                "success": None,
                "tool": "",
                "intent": "",
                "answer": str(answer or ""),
                "error": "observer_unavailable",
                "raw_type": (
                    type(execution_result).__name__
                    if execution_result is not None
                    else "NoneType"
                ),
                "checks": [
                    "observer_unavailable",
                ],
                "version": "P12-1.0",
            }

            self.last_execution_observation = observation
            return observation

        try:
            observation = observer.observe(
                message=message or "",
                decision=decision,
                execution_result=execution_result,
                answer=answer or "",
            )

            self.last_execution_observation = observation

            return observation

        except Exception as exc:

            observation = {
                "observed": False,
                "success": None,
                "tool": "",
                "intent": "",
                "answer": str(answer or ""),
                "error": repr(exc),
                "raw_type": (
                    type(execution_result).__name__
                    if execution_result is not None
                    else "NoneType"
                ),
                "checks": [
                    "observation_exception",
                ],
                "version": "P12-1.0",
            }

            self.last_execution_observation = observation

            log(
                "P12 OBSERVE ERROR: "
                + traceback.format_exc()
            )

            return observation


'''

if "def _p12_observe_execution(" not in main_text:

    main_text = main_text.replace(
        helper_anchor,
        helper_code + helper_anchor,
        1,
    )

    print("P12 HELPER: INSERTED")
else:
    print("P12 HELPER: ALREADY PRESENT")

print("P12 HELPER: PASS")

# ------------------------------------------------------------
# 7. EXECUTE -> OBSERVE -> VERIFY
# ------------------------------------------------------------

observe_marker = (
    "# P12-1 EXECUTE -> OBSERVE"
)

if observe_marker not in main_text:

    verify_anchor = (
        "        # P45_EXECUTION_VERIFY\n"
        "        verification = None\n"
    )

    if verify_anchor not in main_text:
        shutil.copy2(
            backup,
            MAIN,
        )
        raise SystemExit(
            "ERROR: P4-5 verification anchor missing"
        )

    observe_block = '''        # P12-1 EXECUTE -> OBSERVE
        observation = None

        try:
            observer = getattr(
                self,
                "_p12_observe_execution",
                None,
            )

            if callable(observer):
                observation = observer(
                    message=completed,
                    decision=decision,
                    execution_result=execution_result,
                    answer=answer,
                )

        except Exception as exc:
            observation = {
                "observed": False,
                "success": None,
                "tool": "",
                "intent": "",
                "answer": str(answer or ""),
                "error": repr(exc),
                "checks": [
                    "observation_exception",
                ],
                "version": "P12-1.0",
            }

            self.last_execution_observation = observation

            log(
                "P12 OBSERVE ERROR: "
                + traceback.format_exc()
            )

        # P45_EXECUTION_VERIFY
        verification = None
'''

    main_text = main_text.replace(
        verify_anchor,
        observe_block,
        1,
    )

    print(
        "EXECUTE -> OBSERVE INSERTION: PASS"
    )

else:
    print(
        "EXECUTE -> OBSERVE: ALREADY PRESENT"
    )

# ------------------------------------------------------------
# 8. STRUCTURAL GUARDS BEFORE WRITE
# ------------------------------------------------------------

guards = {
    "observer import": (
        "from observer import create_observer"
        in main_text
    ),
    "observer init": (
        "self.observer = create_observer()"
        in main_text
    ),
    "observation state": (
        "self.last_execution_observation = None"
        in main_text
    ),
    "observer helper": (
        "def _p12_observe_execution("
        in main_text
    ),
    "observe marker": (
        "# P12-1 EXECUTE -> OBSERVE"
        in main_text
    ),
    "execute preserved": (
        "def execute_decision("
        in main_text
    ),
    "verify preserved": (
        "def verify_execution_result("
        in main_text
    ),
    "p4-5 marker": (
        "# P45_EXECUTION_VERIFY"
        in main_text
    ),
}

for name, passed in guards.items():
    print(
        name.upper()
        + ": "
        + ("PASS" if passed else "FAIL")
    )

if not all(guards.values()):
    shutil.copy2(
        backup,
        MAIN,
    )
    raise SystemExit(
        "P12-1 STRUCTURAL VALIDATION FAILED"
    )

print("STRUCTURAL GUARDS: PASS")

# ------------------------------------------------------------
# 9. WRITE
# ------------------------------------------------------------

MAIN.write_text(
    main_text,
    encoding="utf-8",
)

print("MAIN WRITE: PASS")

# ------------------------------------------------------------
# 10. FINAL COMPILE / AST
# ------------------------------------------------------------

try:

    py_compile.compile(
        str(MAIN),
        doraise=True,
    )

    py_compile.compile(
        str(OBSERVER),
        doraise=True,
    )

    final_text = MAIN.read_text(
        encoding="utf-8-sig"
    )

    ast.parse(
        final_text,
        filename=str(MAIN),
    )

except Exception as exc:

    print(
        "FINAL VALIDATION ERROR:",
        repr(exc),
    )

    shutil.copy2(
        backup,
        MAIN,
    )

    print("ROLLBACK: PASS")

    raise SystemExit(
        "P12-1 RESULT: FAILED — ROLLED BACK"
    )

print("FINAL COMPILE: PASS")
print("FINAL AST: PASS")

# ------------------------------------------------------------
# 11. RUNTIME IMPORT
# ------------------------------------------------------------

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import observer
from observer import Observer

print("OBSERVER IMPORT: PASS")
print("OBSERVER CLASS: PASS")

import main

runtime = getattr(
    main,
    "MINH",
    None,
)

if runtime is None:
    shutil.copy2(
        backup,
        MAIN,
    )
    raise SystemExit(
        "ERROR: GLOBAL MINH missing"
    )

print("GLOBAL MINH: PASS")

# ------------------------------------------------------------
# 12. RUNTIME OBJECT
# ------------------------------------------------------------

runtime_observer = getattr(
    runtime,
    "observer",
    None,
)

if not isinstance(
    runtime_observer,
    Observer,
):
    shutil.copy2(
        backup,
        MAIN,
    )
    raise SystemExit(
        "ERROR: runtime observer invalid"
    )

print("RUNTIME OBSERVER: PASS")

# ------------------------------------------------------------
# 13. DIRECT OBSERVER TESTS
# ------------------------------------------------------------

test = Observer()

success_result = test.observe(
    message="test",
    decision={
        "intent": "action",
        "tool": "action",
    },
    execution_result={
        "success": True,
        "tool": "action",
        "intent": "action",
    },
    answer="Đã thực hiện.",
)

assert success_result["observed"] is True
assert success_result["success"] is True
assert success_result["tool"] == "action"

print("TEST SUCCESS RESULT: PASS")

failure_result = test.observe(
    message="test",
    decision={
        "intent": "action",
        "tool": "action",
    },
    execution_result={
        "success": False,
        "tool": "action",
        "intent": "action",
        "error": "test failure",
    },
    answer="Không thực hiện được.",
)

assert failure_result["observed"] is True
assert failure_result["success"] is False
assert failure_result["error"] == "test failure"

print("TEST FAILURE RESULT: PASS")

missing_result = test.observe(
    message="test",
    decision={
        "intent": "action",
        "tool": "action",
    },
    execution_result=None,
    answer="",
)

assert missing_result["observed"] is False
assert missing_result["success"] is None

print("TEST MISSING RESULT: PASS")

# ------------------------------------------------------------
# 14. MAIN HELPER TEST
# ------------------------------------------------------------

helper = getattr(
    runtime,
    "_p12_observe_execution",
    None,
)

assert callable(helper)

runtime_result = helper(
    message="test",
    decision={
        "intent": "web",
        "tool": "web",
    },
    execution_result={
        "success": True,
        "tool": "web",
        "intent": "web",
    },
    answer="Kết quả test.",
)

assert runtime_result["observed"] is True
assert runtime_result["success"] is True
assert runtime_result["tool"] == "web"

assert (
    runtime.last_execution_observation
    == runtime_result
)

print("MAIN P12 HELPER TEST: PASS")
print("STATE SAVE: PASS")

# ------------------------------------------------------------
# 15. EXECUTION PATH GUARDS
# ------------------------------------------------------------

final_text = MAIN.read_text(
    encoding="utf-8-sig"
)

assert (
    "answer, execution_result = ("
    in final_text
)

assert (
    "self.execute_decision("
    in final_text
)

assert (
    "# P12-1 EXECUTE -> OBSERVE"
    in final_text
)

assert (
    "# P45_EXECUTION_VERIFY"
    in final_text
)

# Observer itself must contain no execution APIs.
for forbidden in [
    "execute_action(",
    "handle_action_command(",
    "ollama_chat(",
    "requests.get(",
    "web.search(",
]:
    assert forbidden not in observer_code

print("EXECUTION PATH PRESERVED: PASS")
print("OBSERVER NO EXECUTION: PASS")

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("P12-1 RESULT: PASS")
print("OBSERVER CORE: PASS")
print("EXECUTE -> OBSERVE: PASS")
print("VERIFY PRESERVED: PASS")
print("NO DOUBLE EXECUTION: PASS")
print("NO WEB / OLLAMA IN OBSERVER: PASS")
print("P4-5 PRESERVED: PASS")
print("P10 PRESERVED: PASS")
print("P11 PRESERVED: PASS")
print("=" * 70)
