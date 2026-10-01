from pathlib import Path
import ast
import py_compile
import shutil
import importlib

MAIN = Path("main.py")

print("=" * 80)
print("P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE")
print("SAFE INTEGRATION PATCH")
print("=" * 80)

# ------------------------------------------------------------
# 1. PRECHECK
# ------------------------------------------------------------

if not MAIN.exists():
    raise SystemExit("ERROR: main.py not found")

source = MAIN.read_text(encoding="utf-8-sig")

ast.parse(source)
print("MAIN PRECHECK AST: PASS")

py_compile.compile(
    str(MAIN),
    doraise=True,
)
print("MAIN PRECHECK COMPILE: PASS")

required = [
    "def execute_decision(",
    "def _p11_select_tool(",
    "last_p11_tool_selection",
    "last_execution_contract",
    "P12-1 EXECUTE -> OBSERVE",
    "P45_EXECUTION_VERIFY",
    "P10-4 EVALUATION",
]

for marker in required:
    if marker not in source:
        raise SystemExit(
            "ERROR: required marker missing: " + marker
        )

print("REQUIRED ANCHORS: PASS")

# ------------------------------------------------------------
# 2. DUPLICATE GUARD
# ------------------------------------------------------------

if "P12-2 TOOL SELECTION BRIDGE" in source:
    raise SystemExit(
        "ERROR: P12-2 already exists. "
        "No duplicate patch allowed."
    )

# ------------------------------------------------------------
# 3. BACKUP
# ------------------------------------------------------------

backup = Path("main.py.before_p12_2")

if backup.exists():
    raise SystemExit(
        "ERROR: backup already exists: "
        + str(backup)
    )

shutil.copy2(MAIN, backup)

print("BACKUP CREATED:", backup.name)

# ------------------------------------------------------------
# 4. INSERT P12-2 HELPER
# ------------------------------------------------------------

helper_anchor = "    def _p11_select_tool("

if helper_anchor not in source:
    raise SystemExit(
        "ERROR: _p11_select_tool anchor not found"
    )

helper = r'''
    # --------------------------------------------------------
    # P12-2 TOOL SELECTION BRIDGE
    # Judge -> Tool Selector -> Execute
    # SELECT ONLY; NEVER EXECUTE FROM SELECTOR
    # --------------------------------------------------------
    def _p12_2_prepare_tool_selection(
        self,
        message=None,
        decision=None,
        result=None,
    ):
        """
        Prepare the P11 tool selection before execution.

        Safety contract:
        - P11 selector does not execute anything.
        - Existing decision remains authoritative.
        - A selector mismatch is recorded, not guessed away.
        - Execution Contract / clarification gate remains authoritative.
        """

        selection = None

        try:
            selector = getattr(
                self,
                "tool_selector",
                None,
            )

            if selector is None:
                selection = {
                    "tool": None,
                    "reason": "tool_selector_unavailable",
                    "confidence": 0.0,
                    "allowed": False,
                    "advisory_only": True,
                    "version": "P12-2.0",
                    "checks": [
                        "selector_unavailable",
                    ],
                }

                self.last_p11_tool_selection = selection
                return selection

            decision_tool = get_decision_value(
                decision,
                "tool",
                "",
            )

            decision_intent = get_decision_value(
                decision,
                "intent",
                "",
            )

            selection = self._p11_select_tool(
                goal=None,
                plan=None,
                decision=decision,
                result=result,
            )

            if not isinstance(selection, dict):
                selection = {
                    "tool": None,
                    "reason": "invalid_selector_result",
                    "confidence": 0.0,
                    "allowed": False,
                    "advisory_only": True,
                    "version": "P12-2.0",
                    "checks": [
                        "invalid_selector_result",
                    ],
                }

            selected_tool = str(
                selection.get("tool") or ""
            ).strip()

            selection = dict(selection)

            selection["decision_tool"] = (
                str(decision_tool or "").strip()
            )

            selection["decision_intent"] = (
                str(decision_intent or "").strip()
            )

            if selected_tool and decision_tool:
                selection["tool_match"] = (
                    selected_tool == str(
                        decision_tool
                    ).strip()
                )
            else:
                selection["tool_match"] = True

            if (
                selected_tool
                and decision_tool
                and selected_tool != str(
                    decision_tool
                ).strip()
            ):
                selection["checks"] = list(
                    selection.get("checks") or []
                )
                selection["checks"].append(
                    "tool_mismatch"
                )
                selection["reason"] = (
                    str(
                        selection.get("reason")
                        or ""
                    )
                    + " | decision_tool="
                    + str(decision_tool)
                    + " | selected_tool="
                    + selected_tool
                )

            selection["advisory_only"] = True
            selection["bridge_version"] = (
                "P12-2.0"
            )

            self.last_p11_tool_selection = selection

            return selection

        except Exception as exc:
            selection = {
                "tool": None,
                "reason": "tool_selection_exception",
                "confidence": 0.0,
                "allowed": False,
                "advisory_only": True,
                "version": "P12-2.0",
                "checks": [
                    "tool_selection_exception",
                ],
                "error": repr(exc),
            }

            self.last_p11_tool_selection = selection

            log(
                "P12-2 TOOL SELECTION ERROR: "
                + repr(exc)
            )

            return selection

'''

source = source.replace(
    helper_anchor,
    helper + helper_anchor,
    1,
)

print("P12-2 HELPER: INSERTED")

# ------------------------------------------------------------
# 5. INSERT PRE-EXECUTION BRIDGE
# ------------------------------------------------------------

execute_anchor = '''        # ----------------------------------------------------
        # 5. EXECUTION
        # ----------------------------------------------------

        answer, execution_result = (
            self.execute_decision(
                completed,
                decision,
            )
        )
'''

if execute_anchor not in source:
    raise SystemExit(
        "ERROR: execution anchor not found"
    )

bridge = '''        # ----------------------------------------------------
        # P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE
        # Tool selection MUST happen before execution.
        # Selector is advisory/select-only.
        # Existing decision + contract gate remain authoritative.
        # ----------------------------------------------------
        p12_2_tool_selection = None

        try:
            p12_2_tool_selection = (
                self._p12_2_prepare_tool_selection(
                    message=completed,
                    decision=decision,
                    result=getattr(
                        self,
                        "last_p10_evaluation",
                        None,
                    ),
                )
            )
        except Exception as exc:
            p12_2_tool_selection = {
                "tool": None,
                "reason": "bridge_exception",
                "confidence": 0.0,
                "allowed": False,
                "advisory_only": True,
                "version": "P12-2.0",
                "checks": [
                    "bridge_exception",
                ],
                "error": repr(exc),
            }

            self.last_p11_tool_selection = (
                p12_2_tool_selection
            )

            log(
                "P12-2 TOOL BRIDGE ERROR: "
                + traceback.format_exc()
            )

        # ----------------------------------------------------
        # 5. EXECUTION
        # ----------------------------------------------------

        answer, execution_result = (
            self.execute_decision(
                completed,
                decision,
            )
        )
'''

source = source.replace(
    execute_anchor,
    bridge,
    1,
)

print("P12-2 PRE-EXECUTION BRIDGE: INSERTED")

# ------------------------------------------------------------
# 6. REMOVE OLD POST-EXECUTION SELECTOR HOOK
# ------------------------------------------------------------

old_hook = '''            # P11 TOOL SELECTOR — ADVISORY / SELECT ONLY
            _p11_tool_selection = self._p11_select_tool(
                goal=_p10_goal,
                plan=_p10_plan,
                decision=None,
                result=_p10_result,
            )
'''

if old_hook in source:
    source = source.replace(
        old_hook,
        '''            # P11 TOOL SELECTOR
            # P12-2 moved authoritative pre-execution
            # selection to the execution bridge.
''',
        1,
    )
    print("OLD POST-EXECUTION P11 HOOK: REMOVED")
else:
    print(
        "OLD POST-EXECUTION P11 HOOK: "
        "NOT FOUND — CONTINUE"
    )

# ------------------------------------------------------------
# 7. PRESERVE P11-2 JUDGE CONNECTION
# ------------------------------------------------------------

p112_block = '''            # P11-2 TOOL SELECTOR <- P10 JUDGE DECISION
            _p11_2_evaluation = getattr(self, "last_p10_evaluation", None)
            _p11_2_judge = {}
            if isinstance(_p11_2_evaluation, dict):
                _p11_2_judge = _p11_2_evaluation.get("judge", {})
            _p11_2_decision = None
            if isinstance(_p11_2_judge, dict):
                _p11_2_decision = _p11_2_judge.get("decision")
            _p11_2_tool_selection = self._p11_select_tool(
                goal=None,
                plan=None,
                decision=_p11_2_decision,
                result=_p11_2_evaluation,
            )
            self.last_p11_tool_selection = _p11_2_tool_selection
'''

if p112_block in source:
    source = source.replace(
        p112_block,
        '''            # P11-2 compatibility record.
            # Actual pre-execution selection is performed
            # by P12-2 immediately before execute_decision().
''',
        1,
    )
    print("P11-2 POST-EXECUTION DUPLICATE SELECTOR: REMOVED")
else:
    print(
        "P11-2 BLOCK: NOT FOUND — CONTINUE"
    )

# ------------------------------------------------------------
# 8. WRITE
# ------------------------------------------------------------

MAIN.write_text(
    source,
    encoding="utf-8",
)

print("MAIN WRITE: PASS")

# ------------------------------------------------------------
# 9. VALIDATION
# ------------------------------------------------------------

final_source = MAIN.read_text(
    encoding="utf-8-sig"
)

ast.parse(final_source)
print("FINAL AST: PASS")

py_compile.compile(
    str(MAIN),
    doraise=True,
)
print("FINAL COMPILE: PASS")

# Count critical markers
checks = {
    "P12-2 helper": (
        final_source.count(
            "def _p12_2_prepare_tool_selection("
        ) == 1
    ),
    "P12-2 bridge": (
        final_source.count(
            "P12-2 JUDGE -> TOOL SELECTOR -> EXECUTE"
        ) == 1
    ),
    "execute_decision call": (
        final_source.count(
            "self.execute_decision("
        ) >= 1
    ),
    "P12-1 observer": (
        "P12-1 EXECUTE -> OBSERVE"
        in final_source
    ),
    "P4-5 verify": (
        "P45_EXECUTION_VERIFY"
        in final_source
    ),
    "P10 evaluation": (
        "P10-4 EVALUATION"
        in final_source
    ),
}

for name, ok in checks.items():
    print(
        f"{name}: "
        + ("PASS" if ok else "FAIL")
    )

if not all(checks.values()):
    shutil.copy2(
        backup,
        MAIN,
    )
    print("ROLLBACK: PASS")
    raise SystemExit(
        "P12-2 validation failed; main.py restored."
    )

# ------------------------------------------------------------
# 10. IMPORT TEST
# ------------------------------------------------------------

try:
    importlib.invalidate_caches()

    import main

    runtime = getattr(
        main,
        "MINH",
        None,
    )

    if runtime is None:
        raise RuntimeError(
            "global MINH missing"
        )

    print("MAIN IMPORT: PASS")
    print(
        "GLOBAL MINH:",
        type(runtime).__name__,
    )

except Exception as exc:
    shutil.copy2(
        backup,
        MAIN,
    )

    print(
        "IMPORT FAILED — ROLLBACK: PASS"
    )

    raise SystemExit(
        "P12-2 import validation failed: "
        + repr(exc)
    )

# ------------------------------------------------------------
# 11. RUNTIME HELPER TEST — NO EXECUTION
# ------------------------------------------------------------

try:
    selector = getattr(
        runtime,
        "_p12_2_prepare_tool_selection",
        None,
    )

    if not callable(selector):
        raise RuntimeError(
            "P12-2 helper unavailable"
        )

    test_decision = {
        "intent": "web",
        "tool": "web",
    }

    result = selector(
        message="tìm thông tin trên web",
        decision=test_decision,
        result={
            "judge": {
                "decision": "proceed",
            }
        },
    )

    if not isinstance(result, dict):
        raise RuntimeError(
            "selector result is not dict"
        )

    if result.get("advisory_only") is not True:
        raise RuntimeError(
            "advisory_only contract failed"
        )

    if result.get("decision_tool") != "web":
        raise RuntimeError(
            "decision_tool not preserved"
        )

    print("P12-2 HELPER RUNTIME: PASS")
    print(
        "SELECTED TOOL:",
        result.get("tool"),
    )
    print(
        "DECISION TOOL:",
        result.get("decision_tool"),
    )
    print(
        "TOOL MATCH:",
        result.get("tool_match"),
    )

except Exception as exc:
    shutil.copy2(
        backup,
        MAIN,
    )

    print(
        "RUNTIME TEST FAILED — ROLLBACK: PASS"
    )

    raise SystemExit(
        "P12-2 runtime validation failed: "
        + repr(exc)
    )

print()
print("=" * 80)
print("P12-2 RESULT: PASS")
print("JUDGE -> TOOL SELECTOR: CONNECTED")
print("TOOL SELECTION: BEFORE EXECUTE")
print("SELECTOR: ADVISORY / SELECT ONLY")
print("EXECUTION: SINGLE PATH")
print("P12-1 OBSERVER: PRESERVED")
print("P4-5 VERIFY: PRESERVED")
print("P10: PRESERVED")
print("P11: PRESERVED")
print("=" * 80)
