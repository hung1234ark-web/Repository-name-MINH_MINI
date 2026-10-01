from pathlib import Path
import ast
import shutil
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
SELECTOR = ROOT / "tool_selector.py"
BACKUP = ROOT / "main.py.before_p11_1_repair"


def fail(message):
    raise RuntimeError(message)


def read(path):
    return path.read_text(encoding="utf-8-sig")


def write(path, text):
    path.write_text(text, encoding="utf-8")


def compile_source(source, filename):
    compile(source, filename, "exec")


def find_core(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "MinhMiniCore":
            return node
    fail("MinhMiniCore CLASS NOT FOUND")


def find_method(core, name):
    for node in core.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    fail(f"{name} METHOD NOT FOUND")


def create_selector():
    source = r'''from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ToolSelection:
    tool: str | None
    reason: str
    confidence: float
    allowed: bool
    advisory_only: bool = True
    version: str = "P11-1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolSelector:
    VERSION = "P11-1.0"

    def __init__(self):
        self.last_selection = None

    @staticmethod
    def _text(value):
        if value is None:
            return ""
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                parts.append(str(key))
                parts.append(str(item))
            return " ".join(parts).strip().lower()
        if isinstance(value, (list, tuple)):
            return " ".join(str(item) for item in value).strip().lower()
        return str(value).strip().lower()

    def select(
        self,
        *,
        goal=None,
        plan=None,
        decision=None,
        result=None,
    ):
        text = " ".join(
            part
            for part in (
                self._text(goal),
                self._text(plan),
                self._text(decision),
                self._text(result),
            )
            if part
        )

        memory_terms = (
            "nhớ",
            "ghi nhớ",
            "lưu lại",
            "memory",
            "remember",
            "quên",
        )

        if any(term in text for term in memory_terms):
            return self._save(
                "memory",
                "Memory operation detected.",
                0.95,
            )

        time_terms = (
            "mấy giờ",
            "giờ hiện tại",
            "bây giờ là mấy giờ",
            "what time",
            "current time",
        )

        if any(term in text for term in time_terms):
            return self._save(
                "time",
                "Current time requested.",
                0.98,
            )

        date_terms = (
            "hôm nay",
            "ngày bao nhiêu",
            "ngày hôm nay",
            "today",
            "current date",
        )

        if any(term in text for term in date_terms):
            return self._save(
                "date",
                "Current date requested.",
                0.98,
            )

        web_terms = (
            "tìm trên mạng",
            "tìm trên web",
            "google",
            "website",
            "trang web",
            "tin tức",
            "giá",
            "tìm kiếm",
            "search",
            "latest",
            "news",
            "iphone",
        )

        if any(term in text for term in web_terms):
            return self._save(
                "web",
                "External web information requested.",
                0.90,
            )

        web_context_terms = (
            "nghiên cứu",
            "research",
            "phân tích trên web",
            "web context",
        )

        if any(term in text for term in web_context_terms):
            return self._save(
                "web_context",
                "Web context or research requested.",
                0.88,
            )

        action_terms = (
            "mở",
            "đóng",
            "chạy",
            "bật",
            "tắt",
            "click",
            "nhấn",
            "thực hiện",
            "execute",
        )

        if any(term in text for term in action_terms):
            return self._save(
                "action",
                "Executable action appears to be requested.",
                0.82,
            )

        if text:
            return self._save(
                "ollama",
                "No specialized tool matched; reasoning fallback selected.",
                0.55,
            )

        return self._save(
            None,
            "Insufficient information to select a tool.",
            0.0,
            allowed=False,
        )

    def _save(self, tool, reason, confidence, allowed=True):
        selection = ToolSelection(
            tool=tool,
            reason=reason,
            confidence=confidence,
            allowed=allowed,
        ).to_dict()

        self.last_selection = selection
        return dict(selection)


def create_tool_selector():
    return ToolSelector()
'''
    write(SELECTOR, source)
    compile_source(source, str(SELECTOR))


def patch_main():
    original = read(MAIN)

    # ------------------------------------------------------------
    # 1. Parse current main.py FIRST.
    # ------------------------------------------------------------
    compile_source(original, str(MAIN))
    tree = ast.parse(original, filename=str(MAIN))

    core = find_core(tree)
    init = find_method(core, "__init__")
    process = find_method(core, "process")

    init_source = ast.get_source_segment(original, init) or ""
    process_source = ast.get_source_segment(original, process) or ""

    # ------------------------------------------------------------
    # 2. Import ToolSelector safely.
    # ------------------------------------------------------------
    import_line = "from tool_selector import create_tool_selector"

    if import_line not in original:
        future_line = "from __future__ import annotations"

        if future_line not in original:
            fail("FUTURE IMPORT NOT FOUND")

        original = original.replace(
            future_line,
            future_line + "\n\n" + import_line,
            1,
        )

    # ------------------------------------------------------------
    # 3. Reparse after import.
    # ------------------------------------------------------------
    tree = ast.parse(original, filename=str(MAIN))
    core = find_core(tree)
    init = find_method(core, "__init__")
    process = find_method(core, "process")

    init_source = ast.get_source_segment(original, init) or ""
    process_source = ast.get_source_segment(original, process) or ""

    # ------------------------------------------------------------
    # 4. Add selector to __init__.
    # ------------------------------------------------------------
    if "self.tool_selector = create_tool_selector()" not in init_source:

        anchors = [
            "self.last_p10_evaluation = None",
            "self.last_execution_contract = None",
        ]

        anchor = None
        for candidate in anchors:
            if candidate in init_source:
                anchor = candidate
                break

        if anchor is None:
            fail("SAFE INIT ANCHOR NOT FOUND")

        original = original.replace(
            anchor,
            anchor
            + "\n"
            + "        # P11 TOOL SELECTOR — SELECT ONLY\n"
            + "        self.tool_selector = create_tool_selector()\n"
            + "        self.last_p11_tool_selection = None",
            1,
        )

    # ------------------------------------------------------------
    # 5. Reparse.
    # ------------------------------------------------------------
    tree = ast.parse(original, filename=str(MAIN))
    core = find_core(tree)
    process = find_method(core, "process")

    process_source = ast.get_source_segment(original, process) or ""

    # ------------------------------------------------------------
    # 6. Add P11 helper method INSIDE class.
    #
    # This avoids touching the complicated process try/except body.
    # ------------------------------------------------------------
    helper_name = "_p11_select_tool"

    if helper_name not in process_source and helper_name not in original:

        process_end = getattr(process, "end_lineno", process.lineno)

        lines = original.splitlines(keepends=True)

        insert_at = process_end

        # Find next class method indentation boundary.
        class_end = core.end_lineno

        helper = (
            "\n"
            "    # P11 TOOL SELECTOR — SELECT ONLY\n"
            "    def _p11_select_tool(self, goal=None, plan=None, decision=None, result=None):\n"
            "        selector = getattr(self, \"tool_selector\", None)\n"
            "        if selector is None:\n"
            "            return None\n"
            "        selection = selector.select(\n"
            "            goal=goal,\n"
            "            plan=plan,\n"
            "            decision=decision,\n"
            "            result=result,\n"
            "        )\n"
            "        self.last_p11_tool_selection = selection\n"
            "        return selection\n"
        )

        # Insert before make_clarification if present, otherwise before
        # the first top-level function after the class.
        marker = "    def make_clarification("
        if marker in original:
            original = original.replace(
                marker,
                helper + "\n" + marker,
                1,
            )
        else:
            fail("SAFE CLASS METHOD INSERTION ANCHOR NOT FOUND")

    # ------------------------------------------------------------
    # 7. Do NOT insert into the process try/except.
    #
    # Instead add one call immediately after the existing P10 hook
    # block only if a safe standalone state marker exists.
    # ------------------------------------------------------------
    tree = ast.parse(original, filename=str(MAIN))
    core = find_core(tree)
    process = find_method(core, "process")
    process_source = ast.get_source_segment(original, process) or ""

    if "self._p11_select_tool(" not in process_source:

        # We deliberately use the existing P10 evaluation call as a
        # structural anchor, but place P11 immediately BEFORE the
        # P10 call only when the call is a standalone statement.
        p10_call = "self._p10_4_run_evaluation("

        if p10_call not in process_source:
            fail("P10 EVALUATION ANCHOR NOT FOUND")

        # Find exact source line belonging to the call.
        process_lines = process_source.splitlines()

        target_index = None
        for index, line in enumerate(process_lines):
            if p10_call in line:
                target_index = index
                break

        if target_index is None:
            fail("P10 CALL LINE NOT FOUND")

        # Determine indentation from the exact source line.
        target_line = process_lines[target_index]
        indent = target_line[: len(target_line) - len(target_line.lstrip())]

        # Only insert if the P10 call is itself at normal statement
        # indentation. This avoids breaking nested try blocks.
        if len(indent) < 8:
            fail("P10 CALL IS NOT AT SAFE METHOD STATEMENT INDENT")

        insertion = (
            indent
            + "# P11 TOOL SELECTOR — ADVISORY / SELECT ONLY\n"
            + indent
            + "_p11_tool_selection = self._p11_select_tool(\n"
            + indent
            + "    goal=_p10_goal,\n"
            + indent
            + "    plan=_p10_plan,\n"
            + indent
            + "    decision=None,\n"
            + indent
            + "    result=_p10_result,\n"
            + indent
            + ")\n"
        )

        # Reconstruct only the process method source.
        process_lines.insert(target_index, insertion.rstrip("\n"))

        new_process = "\n".join(process_lines)

        old_process = process_source

        if old_process not in original:
            fail("PROCESS SOURCE REPLACEMENT ANCHOR LOST")

        original = original.replace(
            old_process,
            new_process,
            1,
        )

    # ------------------------------------------------------------
    # 8. Hard execution guards.
    # ------------------------------------------------------------
    forbidden = (
        "self.tool_selector.execute(",
        "self.tool_selector.run(",
        "self.tool_selector.call(",
        "self._p11_select_tool().execute(",
        "self._p11_select_tool().run(",
    )

    for token in forbidden:
        if token in original:
            fail("P11 EXECUTION BYPASS DETECTED: " + token)

    # ------------------------------------------------------------
    # 9. Final syntax validation BEFORE writing main.py.
    # ------------------------------------------------------------
    compile_source(original, str(MAIN))

    final_tree = ast.parse(original, filename=str(MAIN))
    final_core = find_core(final_tree)
    final_init = find_method(final_core, "__init__")
    final_process = find_method(final_core, "process")

    final_init_source = ast.get_source_segment(original, final_init) or ""
    final_process_source = ast.get_source_segment(original, final_process) or ""

    if "self.tool_selector = create_tool_selector()" not in final_init_source:
        fail("FINAL INIT CHECK FAILED")

    if "self._p11_select_tool(" not in final_process_source:
        fail("FINAL PROCESS P11 CHECK FAILED")

    if "def _p11_select_tool(" not in original:
        fail("FINAL P11 HELPER CHECK FAILED")

    write(MAIN, original)


def runtime_test():
    compile_source(read(MAIN), str(MAIN))

    if "main" in sys.modules:
        del sys.modules["main"]

    import main as main_module

    core = getattr(main_module, "MINH", None)

    if core is None:
        fail("GLOBAL MINH NOT FOUND")

    selector = getattr(core, "tool_selector", None)

    if selector is None:
        fail("MINH.tool_selector NOT FOUND")

    selection = selector.select(
        goal="tìm giá iphone mới nhất",
        plan=None,
        decision=None,
        result=None,
    )

    if not isinstance(selection, dict):
        fail("SELECTOR RESULT IS NOT DICT")

    if selection.get("tool") != "web":
        fail(
            "SELECTOR RESULT WRONG: expected web, got "
            + repr(selection.get("tool"))
        )

    if selection.get("advisory_only") is not True:
        fail("ADVISORY FLAG FAILED")

    helper_result = core._p11_select_tool(
        goal="tìm giá iphone mới nhất",
        plan=None,
        decision=None,
        result=None,
    )

    if not isinstance(helper_result, dict):
        fail("P11 HELPER RESULT IS NOT DICT")

    if helper_result.get("tool") != "web":
        fail("P11 HELPER DID NOT SELECT WEB")

    saved = getattr(core, "last_p11_tool_selection", None)

    if not isinstance(saved, dict):
        fail("last_p11_tool_selection NOT SAVED")

    print("MAIN IMPORT: PASS")
    print("GLOBAL MINH: PASS")
    print("MINH TYPE:", type(core).__name__)
    print("TOOL SELECTOR: PASS")
    print("DIRECT SELECT: PASS")
    print("P11 HELPER: PASS")
    print("STATE SAVE: PASS")
    print("SELECTED TOOL:", selection.get("tool"))
    print("ADVISORY ONLY: PASS")


def main():
    print("=" * 60)
    print("P11-1 TOOL SELECTOR — SAFE REPAIR")
    print("=" * 60)

    if not MAIN.exists():
        fail("main.py NOT FOUND")

    compile_source(read(MAIN), str(MAIN))
    print("MAIN PRECOMPILE: PASS")

    create_selector()
    print("TOOL_SELECTOR: PASS")

    if BACKUP.exists():
        BACKUP.unlink()

    shutil.copy2(MAIN, BACKUP)
    print("BACKUP CREATED:", BACKUP.name)

    try:
        patch_main()
        print("MAIN PATCH: PASS")
        print("MAIN COMPILE: PASS")
        print("MAIN AST: PASS")

        runtime_test()

        print()
        print("=" * 60)
        print("P11-1 RESULT: PASS")
        print("TOOL SELECTOR: INTEGRATED")
        print("SELECT ONLY: PASS")
        print("EXECUTION PATH: UNCHANGED")
        print("P10-4: PRESERVED")
        print("=" * 60)

        return 0

    except Exception as exc:
        print()
        print("P11-1 FAILED — ROLLBACK")

        try:
            if BACKUP.exists():
                shutil.copy2(BACKUP, MAIN)
                compile_source(read(MAIN), str(MAIN))
                print("ROLLBACK: PASS")
        except Exception as rollback_error:
            print("ROLLBACK ERROR:", rollback_error)

        print("ERROR:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
