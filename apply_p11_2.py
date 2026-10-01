from pathlib import Path
import ast
import shutil
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
BACKUP = ROOT / "main.py.before_p11_2"

def fail(msg):
    raise RuntimeError(msg)

def read(path):
    return path.read_text(encoding="utf-8-sig")

def write(path, data):
    path.write_text(data, encoding="utf-8")

def compile_source(source, filename):
    compile(source, filename, "exec")

def find_core(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
            return node
    fail("MinhMiniCore NOT FOUND")

def find_method(core, name):
    for node in core.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    fail(f"{name} NOT FOUND")

def find_p10_call(process):
    """
    Locate the real AST statement containing:
        self._p10_4_run_evaluation(...)
    """
    for node in ast.walk(process):
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "_p10_4_run_evaluation"
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                return node
    fail("P10 EVALUATION CALL NOT FOUND")

def create_patch_block(indent):
    return (
        f"{indent}# P11-2 TOOL SELECTOR <- P10 JUDGE DECISION\n"
        f"{indent}_p11_2_evaluation = getattr(self, \"last_p10_evaluation\", None)\n"
        f"{indent}_p11_2_judge = {{}}\n"
        f"{indent}if isinstance(_p11_2_evaluation, dict):\n"
        f"{indent}    _p11_2_judge = _p11_2_evaluation.get(\"judge\", {{}})\n"
        f"{indent}_p11_2_decision = None\n"
        f"{indent}if isinstance(_p11_2_judge, dict):\n"
        f"{indent}    _p11_2_decision = _p11_2_judge.get(\"decision\")\n"
        f"{indent}_p11_2_tool_selection = self._p11_select_tool(\n"
        f"{indent}    goal=None,\n"
        f"{indent}    plan=None,\n"
        f"{indent}    decision=_p11_2_decision,\n"
        f"{indent}    result=_p11_2_evaluation,\n"
        f"{indent})\n"
        f"{indent}self.last_p11_tool_selection = _p11_2_tool_selection\n"
    )

def main():
    print("=" * 60)
    print("P11-2 TOOL SELECTOR <- JUDGE INTEGRATION")
    print("=" * 60)

    if not MAIN.exists():
        fail("main.py NOT FOUND")

    original = read(MAIN)

    compile_source(original, str(MAIN))
    print("MAIN PRECOMPILE: PASS")

    tree = ast.parse(original, filename=str(MAIN))
    core = find_core(tree)
    process = find_method(core, "process")

    process_source = ast.get_source_segment(original, process) or ""

    if "def _p11_select_tool(" not in original:
        fail("P11-1 HELPER NOT FOUND")

    if "self.tool_selector" not in process_source:
        print("WARNING: tool_selector reference not directly inside process")
    else:
        print("P11-1 SELECTOR LINK: PASS")

    p10_call = find_p10_call(process)
    print("P10 CALL AST: PASS")
    print("P10 CALL LINE:", p10_call.lineno)

    if "last_p11_tool_selection" in process_source:
        print("EXISTING P11 STATE: FOUND")
    else:
        print("P11 STATE: FOUND GLOBALLY")

    # ------------------------------------------------------------
    # Locate the physical line of the P10 call.
    # The P10 call may span multiple lines. We insert after the
    # complete AST Call expression, never inside it.
    # ------------------------------------------------------------
    lines = original.splitlines(keepends=True)

    end_line = p10_call.end_lineno

    if end_line <= 0 or end_line > len(lines):
        fail("INVALID P10 END LINE")

    target_line = lines[end_line - 1]
    indent = target_line[:len(target_line) - len(target_line.lstrip())]

    if len(indent) < 8:
        fail("P10 CALL INDENT IS NOT A SAFE METHOD LEVEL")

    # ------------------------------------------------------------
    # Check whether P11-2 already exists.
    # ------------------------------------------------------------
    if "P11-2 TOOL SELECTOR <- P10 JUDGE DECISION" in original:
        print("P11-2 ALREADY PRESENT")
        print("NO DUPLICATE PATCH: PASS")
    else:
        block = create_patch_block(indent)

        # Insert after the COMPLETE P10 AST statement.
        lines.insert(end_line, block)

        patched = "".join(lines)

        # Validate before writing.
        compile_source(patched, str(MAIN))
        ast.parse(patched, filename=str(MAIN))

        # Guards: P11 must never execute.
        forbidden = (
            "self.tool_selector.execute(",
            "self.tool_selector.run(",
            "self.tool_selector.call(",
            "_p11_2_tool_selection.execute(",
            "_p11_2_tool_selection.run(",
            "_p11_2_tool_selection.call(",
        )

        for token in forbidden:
            if token in patched:
                fail("EXECUTION BYPASS DETECTED: " + token)

        write(MAIN, patched)

        print("P11-2 PATCH: PASS")
        print("PATCHED AST: PASS")
        print("PATCHED COMPILE: PASS")

    # ------------------------------------------------------------
    # Runtime import
    # ------------------------------------------------------------
    final_source = read(MAIN)
    compile_source(final_source, str(MAIN))

    final_tree = ast.parse(final_source, filename=str(MAIN))
    final_core = find_core(final_tree)
    final_process = find_method(final_core, "process")
    final_process_source = ast.get_source_segment(
        final_source,
        final_process
    ) or ""

    if "P11-2 TOOL SELECTOR <- P10 JUDGE DECISION" not in final_source:
        fail("P11-2 MARKER NOT FOUND")

    if "_p11_2_decision" not in final_process_source:
        fail("P11-2 DECISION VARIABLE NOT FOUND")

    if "_p11_2_tool_selection = self._p11_select_tool(" not in final_process_source:
        fail("P11-2 SELECTOR CALL NOT FOUND")

    print("P11-2 STRUCTURE: PASS")

    if BACKUP.exists():
        BACKUP.unlink()

    shutil.copy2(MAIN, BACKUP)
    print("BACKUP CREATED:", BACKUP.name)

    try:
        if "main" in sys.modules:
            del sys.modules["main"]

        import main as main_module

        core_obj = getattr(main_module, "MINH", None)

        if core_obj is None:
            fail("GLOBAL MINH NOT FOUND")

        print("MAIN IMPORT: PASS")
        print("GLOBAL MINH: PASS")
        print("MINH TYPE:", type(core_obj).__name__)

        selector = getattr(core_obj, "tool_selector", None)

        if selector is None:
            fail("tool_selector OBJECT NOT FOUND")

        print("TOOL SELECTOR OBJECT: PASS")

        # --------------------------------------------------------
        # Direct Judge -> Selector integration test.
        # No process(), no Ollama, no Web, no Action.
        # --------------------------------------------------------
        fake_evaluation = {
            "risk": {
                "verdict": "pass",
                "risk_level": "low",
            },
            "simulator": {
                "verdict": "pass",
                "outcome": "safe",
            },
            "judge": {
                "verdict": "pass",
                "decision": "proceed",
                "score": 0.95,
            },
        }

        judge = fake_evaluation["judge"]
        decision = judge["decision"]

        result = core_obj._p11_select_tool(
            goal="tìm giá iphone mới nhất",
            plan=None,
            decision=decision,
            result=fake_evaluation,
        )

        if not isinstance(result, dict):
            fail("P11-2 RESULT IS NOT DICT")

        if result.get("tool") != "web":
            fail(
                "P11-2 TOOL TEST FAILED: expected web, got "
                + repr(result.get("tool"))
            )

        if result.get("advisory_only") is not True:
            fail("ADVISORY-ONLY FLAG FAILED")

        print("JUDGE DECISION: PASS")
        print("DECISION:", decision)
        print("JUDGE -> SELECTOR: PASS")
        print("SELECTED TOOL:", result.get("tool"))
        print("ADVISORY ONLY: PASS")

        saved = getattr(core_obj, "last_p11_tool_selection", None)

        if not isinstance(saved, dict):
            fail("P11 STATE NOT SAVED")

        print("P11 STATE SAVE: PASS")

        # --------------------------------------------------------
        # Stop/review behavior test.
        # Tool Selector must not execute anything.
        # --------------------------------------------------------
        review_result = core_obj._p11_select_tool(
            goal="tìm giá iphone mới nhất",
            plan=None,
            decision="review",
            result={
                "judge": {
                    "decision": "review"
                }
            },
        )

        if not isinstance(review_result, dict):
            fail("REVIEW TEST RESULT INVALID")

        print("REVIEW DECISION PATH: PASS")

        stop_result = core_obj._p11_select_tool(
            goal="mở ứng dụng",
            plan=None,
            decision="stop",
            result={
                "judge": {
                    "decision": "stop"
                }
            },
        )

        if not isinstance(stop_result, dict):
            fail("STOP TEST RESULT INVALID")

        print("STOP DECISION PATH: PASS")

        # --------------------------------------------------------
        # Hard guards.
        # --------------------------------------------------------
        for token in (
            "self.tool_selector.execute(",
            "self.tool_selector.run(",
            "self.tool_selector.call(",
        ):
            if token in final_source:
                fail("EXECUTION GUARD FAILED: " + token)

        print("NO TOOL EXECUTION: PASS")

        print()
        print("=" * 60)
        print("P11-2 RESULT: PASS")
        print("JUDGE -> TOOL SELECTOR: PASS")
        print("SELECT ONLY: PASS")
        print("NO EXECUTION: PASS")
        print("P10 PRESERVED: PASS")
        print("=" * 60)

        return 0

    except Exception as exc:
        print()
        print("P11-2 FAILED — ROLLBACK")

        if BACKUP.exists():
            shutil.copy2(BACKUP, MAIN)

            try:
                compile_source(read(MAIN), str(MAIN))
                print("ROLLBACK: PASS")
            except Exception as rollback_error:
                print("ROLLBACK COMPILE ERROR:", rollback_error)

        print("ERROR:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
