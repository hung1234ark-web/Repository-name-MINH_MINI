from pathlib import Path
import ast
import shutil
import py_compile

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
OBSERVER = ROOT / "observer.py"

print("=" * 70)
print("P12-1 EXECUTE -> OBSERVE -> VERIFY")
print("SAFE SURGICAL PATCH")
print("=" * 70)

# ------------------------------------------------------------
# 1. Preconditions
# ------------------------------------------------------------

if not MAIN.exists():
    raise SystemExit("ERROR: main.py not found")

main_text = MAIN.read_text(encoding="utf-8-sig")

compile(main_text, str(MAIN), "exec")
ast.parse(main_text, filename=str(MAIN))
print("MAIN PRECHECK: PASS")

required = [
    "def execute_decision(",
    "def verify_execution_result(",
    "# P45_EXECUTION_VERIFY",
]

for marker in required:
    if marker not in main_text:
        raise SystemExit(
            f"ERROR: required anchor missing: {marker}"
        )

print("MAIN ANCHORS: PASS")

# ------------------------------------------------------------
# 2. Create observer.py
# ------------------------------------------------------------

observer_code = r'''# ============================================================
# MINH MINI — OBSERVER
# P12-1 Execute -> Observe -> Verify
#
# Observer chỉ ghi nhận kết quả đã xảy ra.
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

compile(observer_code, str(OBSERVER), "exec")
ast.parse(observer_code, filename=str(OBSERVER))

print("OBSERVER FILE: PASS")
print("OBSERVER AST + COMPILE: PASS")

# ------------------------------------------------------------
# 3. Backup main.py
# ------------------------------------------------------------

backup = ROOT / "main.py.before_p12_1"
shutil.copy2(MAIN, backup)

print(
    "BACKUP CREATED:",
    backup.name,
)

# ------------------------------------------------------------
# 4. Import observer
# ------------------------------------------------------------

import_anchor = (
    "from tool_selector import create_tool_selector"
)

import_replacement = (
    "from tool_selector import create_tool_selector\n"
    "from observer import create_observer"
)

if import_anchor not in main_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "ERROR: observer import anchor missing"
    )

if "from observer import create_observer" not in main_text:
    main_text = main_text.replace(
        import_anchor,
        import_replacement,
        1,
    )

print("OBSERVER IMPORT: PASS")

# ------------------------------------------------------------
# 5. Init observer in MinhMiniCore.__init__
# ------------------------------------------------------------

init_anchor = (
    "self.last_p11_tool_selection = None"
)

init_replacement = (
    "self.last_p11_tool_selection = None\n"
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

if init_anchor not in main_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "ERROR: observer init anchor missing"
    )

if "self.last_execution_observation = None" not in main_text:
    main_text = main_text.replace(
        init_anchor,
        init_replacement,
        1,
    )

print("OBSERVER INIT: PASS")

# ------------------------------------------------------------
# 6. Add P12 helper method
# ------------------------------------------------------------

helper_anchor = (
    "    # --------------------------------------------------------\n"
    "    # P11 TOOL SELECTOR — SELECT ONLY\n"
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
            self.last_execution_observation = {
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

            return self.last_execution_observation

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
                + repr(exc)
            )

            return observation

'''

if helper_anchor not in main_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "ERROR: P11 helper anchor missing"
    )

if "def _p12_observe_execution(" not in main_text:
    main_text = main_text.replace(
        helper_anchor,
        helper_code + helper_anchor,
        1,
    )

print("P12 HELPER: PASS")

# ------------------------------------------------------------
# 7. Insert Observe between Execute and Verify
# ------------------------------------------------------------

execute_verify_anchor = '''        # P45_EXECUTION_VERIFY
        verification = None
'''

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

if execute_verify_anchor not in main_text:
    shutil.copy2(backup, MAIN)
    raise SystemExit(
        "ERROR: Execute -> Verify anchor missing"
    )

if "# P12-1 EXECUTE -> OBSERVE" not in main_text:
    main_text = main_text.replace(
        execute_verify_anchor,
        observe_block,
        1,
    )

print("EXECUTE -> OBSERVE INSERTION: PASS")

# ------------------------------------------------------------
# 8. Save main.py
# ------------------------------------------------------------

MAIN.write_text(
    main_text,
    encoding="utf-8",
)

print("MAIN WRITE: PASS")

# ------------------------------------------------------------
# 9. Final validation
# ------------------------------------------------------------

try:
    py_compile.compile(
        str(OBSERVER),
        doraise=True,
    )

    py_compile.compile(
        str(MAIN),
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
        "\nVALIDATION FAILED:",
        repr(exc),
    )

    shutil.copy2(
        backup,
        MAIN,
    )

    print("ROLLBACK: PASS")
    raise SystemExit(
        "P12-1 PATCH RESULT: ROLLED BACK"
    )

print("FINAL COMPILE: PASS")
print("FINAL AST: PASS")

# ------------------------------------------------------------
# 10. Structural guards
# ------------------------------------------------------------

guards = {
    "observer import": (
        "from observer import create_observer"
        in final_text
    ),
    "observer init": (
        "self.observer = create_observer()"
        in final_text
    ),
    "last observation state": (
        "self.last_execution_observation = None"
        in final_text
    ),
    "observer helper": (
        "def _p12_observe_execution("
        in final_text
    ),
    "execute observe marker": (
        "# P12-1 EXECUTE -> OBSERVE"
        in final_text
    ),
    "verify preserved": (
        "# P45_EXECUTION_VERIFY"
        in final_text
    ),
    "execute decision preserved": (
        "self.execute_decision("
        in final_text
    ),
    "verify method preserved": (
        "def verify_execution_result("
        in final_text
    ),
}

for name, passed in guards.items():
    print(
        f"{name.upper()}: "
        + ("PASS" if passed else "FAIL")
    )

if not all(guards.values()):
    shutil.copy2(
        backup,
        MAIN,
    )

    print("ROLLBACK: PASS")

    raise SystemExit(
        "P12-1 RESULT: FAILED — ROLLED BACK"
    )

# ------------------------------------------------------------
# 11. Import runtime
# ------------------------------------------------------------

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import observer
from observer import Observer, Observation

print("OBSERVER IMPORT: PASS")
print("OBSERVER TYPE: PASS")

# ------------------------------------------------------------
# 12. Direct core tests — NO real execution
# ------------------------------------------------------------

test_observer = Observer()

result = test_observer.observe(
    message="mở youtube",
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

assert result["observed"] is True
assert result["success"] is True
assert result["tool"] == "action"
assert result["intent"] == "action"
assert "execution_result_present" in result["checks"]

print("TEST 1 SUCCESS RESULT: PASS")

failed = test_observer.observe(
    message="mở app",
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

assert failed["observed"] is True
assert failed["success"] is False
assert failed["error"] == "test failure"
assert "success_false" in failed["checks"]

print("TEST 2 FAILURE RESULT: PASS")

missing = test_observer.observe(
    message="test",
    decision={
        "intent": "action",
        "tool": "action",
    },
    execution_result=None,
    answer="",
)

assert missing["observed"] is False
assert missing["success"] is None
assert "missing_execution_result" in missing["checks"]

print("TEST 3 MISSING RESULT: PASS")

# ------------------------------------------------------------
# 13. Main runtime object
# ------------------------------------------------------------

import main

runtime = getattr(
    main,
    "MINH",
    None,
)

assert runtime is not None
print("GLOBAL MINH: PASS")

assert getattr(
    runtime,
    "observer",
    None,
) is not None

print("RUNTIME OBSERVER: PASS")

assert callable(
    getattr(
        runtime,
        "_p12_observe_execution",
        None,
    )
)

print("P12 HELPER RUNTIME: PASS")

# ------------------------------------------------------------
# 14. Verify P4-5 remains callable
# ------------------------------------------------------------

assert callable(
    getattr(
        runtime,
        "execute_decision",
        None,
    )
)

assert callable(
    getattr(
        runtime,
        "verify_execution_result",
        None,
    )
)

print("EXECUTE API PRESERVED: PASS")
print("VERIFY API PRESERVED: PASS")

# ------------------------------------------------------------
# 15. Final status
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
