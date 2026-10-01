from pathlib import Path
import ast
import py_compile
import importlib
import shutil
import sys

ROOT = Path.cwd()
MAIN = ROOT / "main.py"
LIFECYCLE = ROOT / "lifecycle.py"
BACKUP = ROOT / "main.py.before_p12_3_lifecycle"

print("=" * 100)
print("P12-3 RUNTIME LIFECYCLE")
print("EXECUTE -> OBSERVE -> VERIFY")
print("SURGICAL PATCH / ROLLBACK SAFE")
print("=" * 100)

# ------------------------------------------------------------
# 1. PRECHECK
# ------------------------------------------------------------

if not MAIN.exists():
    raise SystemExit("ERROR: main.py missing")

source = MAIN.read_text(encoding="utf-8-sig")

try:
    ast.parse(source)
    print("MAIN PRECHECK AST: PASS")
except Exception as exc:
    raise SystemExit(f"MAIN PRECHECK AST: FAIL: {exc}")

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
    print("MAIN PRECHECK COMPILE: PASS")
except Exception as exc:
    raise SystemExit(f"MAIN PRECHECK COMPILE: FAIL: {exc}")

required_anchors = [
    "def _p12_2_prepare_tool_selection(",
    "# P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE",
    "# P12-1 EXECUTE -> OBSERVE",
    "# P45_EXECUTION_VERIFY",
    "def verify_execution_result(",
    "def execute_decision(",
]

for anchor in required_anchors:
    if anchor not in source:
        raise SystemExit(
            "REQUIRED ANCHOR MISSING: " + anchor
        )

print("REQUIRED P12 ANCHORS: PASS")

# ------------------------------------------------------------
# 2. CREATE LIFECYCLE MODULE
# ------------------------------------------------------------

lifecycle_code = r'''# ============================================================
# MINH MINI — EXECUTION LIFECYCLE
# P12-3 Runtime Lifecycle
#
# Tracks:
# P12-2 PREPARE
# EXECUTE
# OBSERVE
# VERIFY
#
# This module records lifecycle state only.
# It NEVER executes tools.
# It NEVER calls Web.
# It NEVER calls Ollama.
# It NEVER calls Action.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


VERSION = "P12-3.0"


@dataclass(frozen=True)
class LifecycleRecord:
    status: str
    stages: list[str]
    completed_stages: list[str]
    failed_stage: str
    verified: bool | None
    success: bool | None
    tool: str
    intent: str
    checks: list[str]
    version: str = VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionLifecycle:
    VERSION = VERSION

    EXPECTED_ORDER = (
        "prepare",
        "execute",
        "observe",
        "verify",
    )

    def __init__(self):
        self.last_lifecycle: LifecycleRecord | None = None
        self._stages: list[str] = []

    def reset(self) -> None:
        self._stages = []

    def record(self, stage: str) -> dict[str, Any]:
        stage = str(stage or "").strip().lower()

        if stage not in self.EXPECTED_ORDER:
            raise ValueError(
                f"invalid_lifecycle_stage:{stage}"
            )

        expected_index = len(self._stages)

        if expected_index >= len(self.EXPECTED_ORDER):
            raise ValueError(
                "lifecycle_already_complete"
            )

        expected_stage = self.EXPECTED_ORDER[
            expected_index
        ]

        if stage != expected_stage:
            raise ValueError(
                "lifecycle_order_violation:"
                + expected_stage
                + "->"
                + stage
            )

        self._stages.append(stage)

        return {
            "stage": stage,
            "stages": list(self._stages),
            "version": self.VERSION,
        }

    def finalize(
        self,
        *,
        verified: bool | None = None,
        success: bool | None = None,
        tool: str = "",
        intent: str = "",
        error: str = "",
    ) -> dict[str, Any]:

        stages = list(self._stages)
        checks: list[str] = []

        if stages == list(self.EXPECTED_ORDER):
            checks.append("lifecycle_order_pass")
        else:
            checks.append("lifecycle_order_incomplete")

        if verified is True:
            checks.append("verification_pass")
        elif verified is False:
            checks.append("verification_fail")
        else:
            checks.append("verification_unknown")

        if success is True:
            checks.append("execution_success")
        elif success is False:
            checks.append("execution_failure")
        else:
            checks.append("execution_unknown")

        if error:
            checks.append("error_present")

        if (
            stages == list(self.EXPECTED_ORDER)
            and verified is True
            and success is True
        ):
            status = "pass"
        elif verified is False or success is False:
            status = "fail"
        else:
            status = "review"

        failed_stage = ""

        if status == "fail":
            if "verify" in stages and verified is False:
                failed_stage = "verify"
            elif "execute" in stages and success is False:
                failed_stage = "execute"
            elif "observe" not in stages:
                failed_stage = "observe"
            elif "execute" not in stages:
                failed_stage = "execute"
            elif "prepare" not in stages:
                failed_stage = "prepare"

        record = LifecycleRecord(
            status=status,
            stages=stages,
            completed_stages=stages,
            failed_stage=failed_stage,
            verified=verified
            if isinstance(verified, bool)
            else None,
            success=success
            if isinstance(success, bool)
            else None,
            tool=str(tool or "").strip(),
            intent=str(intent or "").strip(),
            checks=checks,
        )

        self.last_lifecycle = record
        return record.to_dict()


def create_execution_lifecycle() -> ExecutionLifecycle:
    return ExecutionLifecycle()


__all__ = [
    "VERSION",
    "LifecycleRecord",
    "ExecutionLifecycle",
    "create_execution_lifecycle",
]
'''

LIFECYCLE.write_text(
    lifecycle_code,
    encoding="utf-8",
)

print("LIFECYCLE FILE WRITE: PASS")

# ------------------------------------------------------------
# 3. VALIDATE LIFECYCLE MODULE
# ------------------------------------------------------------

try:
    ast.parse(lifecycle_code)
    print("LIFECYCLE AST: PASS")
except Exception as exc:
    raise SystemExit(
        f"LIFECYCLE AST: FAIL: {exc}"
    )

try:
    py_compile.compile(
        str(LIFECYCLE),
        doraise=True,
    )
    print("LIFECYCLE COMPILE: PASS")
except Exception as exc:
    raise SystemExit(
        f"LIFECYCLE COMPILE: FAIL: {exc}"
    )

# ------------------------------------------------------------
# 4. BACKUP MAIN
# ------------------------------------------------------------

if BACKUP.exists():
    BACKUP.unlink()

shutil.copy2(MAIN, BACKUP)
print(
    "BACKUP CREATED:",
    BACKUP.name,
)

# ------------------------------------------------------------
# 5. IMPORT
# ------------------------------------------------------------

try:
    from lifecycle import (
        ExecutionLifecycle,
        create_execution_lifecycle,
    )

    tracker = create_execution_lifecycle()

    if not isinstance(
        tracker,
        ExecutionLifecycle,
    ):
        raise RuntimeError(
            "lifecycle_factory_invalid"
        )

    print("LIFECYCLE IMPORT: PASS")
    print("LIFECYCLE INIT: PASS")

except Exception as exc:
    raise SystemExit(
        f"LIFECYCLE IMPORT: FAIL: {exc}"
    )

# ------------------------------------------------------------
# 6. PATCH MAIN IMPORT
# ------------------------------------------------------------

import_anchor = "from observer import create_observer"

if import_anchor not in source:
    print(
        "OBSERVER IMPORT ANCHOR: MISSING"
    )
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

if "from lifecycle import create_execution_lifecycle" not in source:
    source = source.replace(
        import_anchor,
        import_anchor
        + "\nfrom lifecycle import create_execution_lifecycle",
        1,
    )

print("MAIN LIFECYCLE IMPORT: PASS")

# ------------------------------------------------------------
# 7. PATCH INIT
# ------------------------------------------------------------

init_anchor = "self.last_execution_observation = None"

if init_anchor not in source:
    print("INIT ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

if "self.execution_lifecycle = create_execution_lifecycle()" not in source:
    source = source.replace(
        init_anchor,
        init_anchor
        + "\n        # P12-3 EXECUTION LIFECYCLE INIT\n"
        + "        try:\n"
        + "            self.execution_lifecycle = create_execution_lifecycle()\n"
        + "        except Exception as exc:\n"
        + "            self.execution_lifecycle = None\n"
        + "            log(\"P12-3 LIFECYCLE INIT ERROR: \" + repr(exc))\n"
        + "        self.last_execution_lifecycle = None",
        1,
    )

print("MAIN LIFECYCLE INIT: PASS")

# ------------------------------------------------------------
# 8. INSERT HELPER
# ------------------------------------------------------------

helper_anchor = "    def _p12_2_prepare_tool_selection("

if helper_anchor not in source:
    print("P12-2 HELPER ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

lifecycle_helper = r'''
    # --------------------------------------------------------
    # P12-3 EXECUTION LIFECYCLE
    # Tracks prepare -> execute -> observe -> verify.
    # SELECT/OBSERVE/LIFECYCLE NEVER EXECUTE TOOLS.
    # --------------------------------------------------------
    def _p12_3_lifecycle_stage(self, stage):
        lifecycle = getattr(
            self,
            "execution_lifecycle",
            None,
        )

        if lifecycle is None:
            return {
                "stage": str(stage or ""),
                "recorded": False,
                "error": "lifecycle_unavailable",
                "version": "P12-3.0",
            }

        try:
            return lifecycle.record(stage)
        except Exception as exc:
            log(
                "P12-3 LIFECYCLE ERROR: "
                + repr(exc)
            )
            return {
                "stage": str(stage or ""),
                "recorded": False,
                "error": repr(exc),
                "version": "P12-3.0",
            }

    def _p12_3_finalize_lifecycle(
        self,
        verification=None,
        execution_result=None,
        decision=None,
    ):
        lifecycle = getattr(
            self,
            "execution_lifecycle",
            None,
        )

        if lifecycle is None:
            result = {
                "status": "review",
                "stages": [],
                "completed_stages": [],
                "failed_stage": "",
                "verified": None,
                "success": None,
                "tool": "",
                "intent": "",
                "checks": [
                    "lifecycle_unavailable",
                ],
                "version": "P12-3.0",
            }
            self.last_execution_lifecycle = result
            return result

        try:
            verified = get_decision_value(
                verification,
                "verified",
                None,
            )

            success = get_decision_value(
                execution_result,
                "success",
                None,
            )

            tool = get_decision_value(
                execution_result,
                "tool",
                get_decision_value(
                    decision,
                    "tool",
                    "",
                ),
            )

            intent = get_decision_value(
                execution_result,
                "intent",
                get_decision_value(
                    decision,
                    "intent",
                    "",
                ),
            )

            error = get_decision_value(
                execution_result,
                "error",
                "",
            )

            result = lifecycle.finalize(
                verified=verified,
                success=success,
                tool=tool,
                intent=intent,
                error=error,
            )

            self.last_execution_lifecycle = result
            return result

        except Exception as exc:
            result = {
                "status": "review",
                "stages": [],
                "completed_stages": [],
                "failed_stage": "",
                "verified": None,
                "success": None,
                "tool": "",
                "intent": "",
                "checks": [
                    "lifecycle_finalize_exception",
                ],
                "error": repr(exc),
                "version": "P12-3.0",
            }

            self.last_execution_lifecycle = result

            log(
                "P12-3 LIFECYCLE FINALIZE ERROR: "
                + repr(exc)
            )

            return result

'''

if "def _p12_3_lifecycle_stage(" not in source:
    source = source.replace(
        helper_anchor,
        lifecycle_helper + helper_anchor,
        1,
    )

print("P12-3 HELPERS: INSERTED")

# ------------------------------------------------------------
# 9. INSERT PREPARE STAGE
# ------------------------------------------------------------

prepare_anchor = (
    "        # ----------------------------------------------------\n"
    "        # 5. EXECUTION\n"
)

if prepare_anchor not in source:
    print("EXECUTION ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

prepare_stage = (
    "        # P12-3 LIFECYCLE: PREPARE\n"
    "        try:\n"
    "            lifecycle = getattr(\n"
    "                self,\n"
    "                \"execution_lifecycle\",\n"
    "                None,\n"
    "            )\n"
    "            if lifecycle is not None:\n"
    "                lifecycle.reset()\n"
    "            self._p12_3_lifecycle_stage(\"prepare\")\n"
    "        except Exception as exc:\n"
    "            log(\"P12-3 PREPARE ERROR: \" + repr(exc))\n"
    "\n"
)

if "# P12-3 LIFECYCLE: PREPARE" not in source:
    source = source.replace(
        prepare_anchor,
        prepare_stage + prepare_anchor,
        1,
    )

print("P12-3 PREPARE STAGE: INSERTED")

# ------------------------------------------------------------
# 10. INSERT EXECUTE STAGE
# ------------------------------------------------------------

execute_anchor = (
    "        answer, execution_result = (\n"
    "            self.execute_decision(\n"
        )

if execute_anchor not in source:
    print("EXECUTE CALL ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

execute_stage = (
    "        # P12-3 LIFECYCLE: EXECUTE\n"
    "        self._p12_3_lifecycle_stage(\"execute\")\n"
    "\n"
)

if "# P12-3 LIFECYCLE: EXECUTE" not in source:
    source = source.replace(
        execute_anchor,
        execute_stage + execute_anchor,
        1,
    )

print("P12-3 EXECUTE STAGE: INSERTED")

# ------------------------------------------------------------
# 11. INSERT OBSERVE STAGE
# ------------------------------------------------------------

observe_anchor = (
    "        # P12-1 EXECUTE -> OBSERVE\n"
)

if observe_anchor not in source:
    print("OBSERVE ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

observe_stage = (
    "        # P12-3 LIFECYCLE: OBSERVE\n"
    "        self._p12_3_lifecycle_stage(\"observe\")\n"
    "\n"
)

if "# P12-3 LIFECYCLE: OBSERVE" not in source:
    source = source.replace(
        observe_anchor,
        observe_stage + observe_anchor,
        1,
    )

print("P12-3 OBSERVE STAGE: INSERTED")

# ------------------------------------------------------------
# 12. INSERT VERIFY + FINALIZE
# ------------------------------------------------------------

verify_end_anchor = (
    "            log(\n"
    "                \"EXECUTION VERIFY ERROR: \"\n"
)

if verify_end_anchor not in source:
    print("VERIFY ERROR ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

# We only add the verify lifecycle stage immediately
# before the existing verification block, then finalize
# immediately after verification try/except.
verify_stage_anchor = (
    "        # P45_EXECUTION_VERIFY\n"
)

if verify_stage_anchor not in source:
    print("P4-5 VERIFY ANCHOR: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

verify_stage = (
    "        # P12-3 LIFECYCLE: VERIFY\n"
    "        self._p12_3_lifecycle_stage(\"verify\")\n"
    "\n"
)

if "# P12-3 LIFECYCLE: VERIFY" not in source:
    source = source.replace(
        verify_stage_anchor,
        verify_stage + verify_stage_anchor,
        1,
    )

# Find the first block after P45 verification that returns
# into normal execution. We use the stable next marker.
next_marker = (
    "        # ----------------------------------------------------\n"
)

verify_pos = source.find(
    verify_stage_anchor
)

if verify_pos < 0:
    print("VERIFY POSITION: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

# Search for the next major marker after verification.
next_pos = source.find(
    next_marker,
    verify_pos + len(verify_stage_anchor),
)

if next_pos < 0:
    print("POST VERIFY MARKER: MISSING")
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(1)

finalize_code = (
    "\n"
    "        # P12-3 LIFECYCLE FINALIZE\n"
    "        try:\n"
    "            self._p12_3_finalize_lifecycle(\n"
    "                verification=verification,\n"
    "                execution_result=execution_result,\n"
    "                decision=decision,\n"
    "            )\n"
    "        except Exception as exc:\n"
    "            log(\"P12-3 FINALIZE ERROR: \" + repr(exc))\n"
    "\n"
)

if "# P12-3 LIFECYCLE FINALIZE" not in source:
    source = source[:next_pos] + finalize_code + source[next_pos:]

print("P12-3 VERIFY + FINALIZE: INSERTED")

# ------------------------------------------------------------
# 13. WRITE + VALIDATE
# ------------------------------------------------------------

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("MAIN WRITE: PASS")

try:
    ast.parse(source)
    print("FINAL AST: PASS")
except Exception as exc:
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(
        f"FINAL AST: FAIL -> ROLLBACK: {exc}"
    )

try:
    py_compile.compile(
        str(MAIN),
        doraise=True,
    )
    print("FINAL COMPILE: PASS")
except Exception as exc:
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(
        f"FINAL COMPILE: FAIL -> ROLLBACK: {exc}"
    )

# ------------------------------------------------------------
# 14. SOURCE GUARDS
# ------------------------------------------------------------

final_source = MAIN.read_text(
    encoding="utf-8-sig"
)

guards = {
    "P12-3 IMPORT":
        "from lifecycle import create_execution_lifecycle"
        in final_source,

    "P12-3 INIT":
        "self.execution_lifecycle = create_execution_lifecycle()"
        in final_source,

    "P12-3 STAGE HELPER":
        "def _p12_3_lifecycle_stage("
        in final_source,

    "P12-3 FINALIZE HELPER":
        "def _p12_3_finalize_lifecycle("
        in final_source,

    "PREPARE STAGE":
        'self._p12_3_lifecycle_stage("prepare")'
        in final_source,

    "EXECUTE STAGE":
        'self._p12_3_lifecycle_stage("execute")'
        in final_source,

    "OBSERVE STAGE":
        'self._p12_3_lifecycle_stage("observe")'
        in final_source,

    "VERIFY STAGE":
        'self._p12_3_lifecycle_stage("verify")'
        in final_source,

    "FINALIZE":
        "self._p12_3_finalize_lifecycle("
        in final_source,

    "P12-2 PRESERVED":
        "# P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE"
        in final_source,

    "P12-1 PRESERVED":
        "# P12-1 EXECUTE -> OBSERVE"
        in final_source,

    "P4-5 PRESERVED":
        "# P45_EXECUTION_VERIFY"
        in final_source,
}

for name, ok in guards.items():
    print(
        f"{name}: {'PASS' if ok else 'FAIL'}"
    )
    if not ok:
        shutil.copy2(BACKUP, MAIN)
        raise SystemExit(
            "STRUCTURAL GUARD FAILED -> ROLLBACK"
        )

# ------------------------------------------------------------
# 15. MAIN IMPORT
# ------------------------------------------------------------

try:
    importlib.invalidate_caches()

    if "main" in sys.modules:
        del sys.modules["main"]

    main_module = importlib.import_module("main")

    print("MAIN IMPORT: PASS")

    minh = getattr(
        main_module,
        "MINH",
        None,
    )

    if minh is None:
        raise RuntimeError(
            "GLOBAL_MINH_MISSING"
        )

    print(
        "GLOBAL MINH:",
        type(minh).__name__,
    )

except Exception as exc:
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(
        f"MAIN IMPORT: FAIL -> ROLLBACK: {exc}"
    )

# ------------------------------------------------------------
# 16. RUNTIME LIFECYCLE TESTS
# ------------------------------------------------------------

try:
    runtime_tracker = (
        create_execution_lifecycle()
    )

    # SUCCESS
    runtime_tracker.reset()

    for stage in (
        "prepare",
        "execute",
        "observe",
        "verify",
    ):
        runtime_tracker.record(stage)

    success_result = runtime_tracker.finalize(
        verified=True,
        success=True,
        tool="web",
        intent="web",
    )

    if success_result["status"] != "pass":
        raise RuntimeError(
            "success_status_not_pass"
        )

    if success_result["stages"] != [
        "prepare",
        "execute",
        "observe",
        "verify",
    ]:
        raise RuntimeError(
            "success_order_invalid"
        )

    print("SUCCESS LIFECYCLE: PASS")

    # FAILURE
    failure_tracker = (
        create_execution_lifecycle()
    )

    for stage in (
        "prepare",
        "execute",
        "observe",
        "verify",
    ):
        failure_tracker.record(stage)

    failure_result = failure_tracker.finalize(
        verified=False,
        success=False,
        tool="action",
        intent="action",
        error="test_failure",
    )

    if failure_result["status"] != "fail":
        raise RuntimeError(
            "failure_status_not_fail"
        )

    print("FAILURE LIFECYCLE: PASS")

    # INCOMPLETE
    incomplete_tracker = (
        create_execution_lifecycle()
    )

    incomplete_tracker.record("prepare")

    incomplete_result = (
        incomplete_tracker.finalize(
            verified=None,
            success=None,
        )
    )

    if incomplete_result["status"] != "review":
        raise RuntimeError(
            "incomplete_status_not_review"
        )

    print("INCOMPLETE LIFECYCLE: PASS")

    # ORDER GUARD
    order_tracker = (
        create_execution_lifecycle()
    )

    order_tracker.record("prepare")

    order_failed = False

    try:
        order_tracker.record("observe")
    except ValueError:
        order_failed = True

    if not order_failed:
        raise RuntimeError(
            "order_guard_failed"
        )

    print("ORDER GUARD: PASS")

    # NO EXECUTION CONTRACT
    lifecycle_source = LIFECYCLE.read_text(
        encoding="utf-8"
    )

    forbidden = [
        "execute_decision",
        "handle_action_command",
        "execute_action",
        "requests.",
        "urllib.",
        "ollama",
        "web.",
    ]

    for token in forbidden:
        if token in lifecycle_source:
            raise RuntimeError(
                "forbidden_execution_token:"
                + token
            )

    print("NO EXECUTION FROM LIFECYCLE: PASS")

except Exception as exc:
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(
        "RUNTIME LIFECYCLE TEST: FAIL -> "
        "ROLLBACK: "
        + repr(exc)
    )

# ------------------------------------------------------------
# 17. MAIN OBJECT RUNTIME
# ------------------------------------------------------------

try:
    runtime_minh = getattr(
        main_module,
        "MINH",
        None,
    )

    lifecycle = getattr(
        runtime_minh,
        "execution_lifecycle",
        None,
    )

    if lifecycle is None:
        raise RuntimeError(
            "MAIN_LIFECYCLE_MISSING"
        )

    if not hasattr(
        runtime_minh,
        "last_execution_lifecycle",
    ):
        raise RuntimeError(
            "MAIN_LIFECYCLE_STATE_MISSING"
        )

    print("MAIN LIFECYCLE OBJECT: PASS")
    print("MAIN LIFECYCLE STATE: PASS")

except Exception as exc:
    shutil.copy2(BACKUP, MAIN)
    raise SystemExit(
        "MAIN RUNTIME STATE: FAIL -> "
        "ROLLBACK: "
        + repr(exc)
    )

# ------------------------------------------------------------
# 18. FINAL
# ------------------------------------------------------------

print("=" * 100)
print("P12-3 RESULT: PASS")
print("EXECUTE -> OBSERVE -> VERIFY LIFECYCLE: PASS")
print("ORDER GUARD: PASS")
print("FAILURE PATH: PASS")
print("INCOMPLETE PATH: PASS")
print("NO EXECUTION FROM LIFECYCLE: PASS")
print("MAIN STATE: PASS")
print("=" * 100)
