from __future__ import annotations

from pathlib import Path
import ast
import shutil
import sys

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
SELECTOR = ROOT / "tool_selector.py"
BACKUP = ROOT / "main.py.before_p11_1"


def fail(message: str) -> None:
    raise RuntimeError(message)


def compile_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8-sig")
    compile(source, str(path), "exec")


def parse_file(path: Path) -> ast.AST:
    source = path.read_text(encoding="utf-8-sig")
    return ast.parse(source, filename=str(path))


def write_selector() -> None:
    selector = r'''# ============================================================
# MINH MINI — P11 TOOL SELECTOR
# TOOL SELECTION ONLY
#
# P11 RULE:
#   SELECT TOOL
#   DO NOT EXECUTE TOOL
#
# Execution remains under the existing execution pipeline.
# ============================================================

from __future__ import annotations

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
    """
    P11 Tool Selector.

    Responsibility:
        Decide WHICH tool should be used.

    Explicitly NOT responsible for:
        - executing tools
        - calling Web
        - calling Ollama
        - performing actions
        - changing execution state
    """

    VERSION = "P11-1.0"

    TOOL_ORDER = (
        "memory",
        "time",
        "date",
        "web",
        "web_context",
        "action",
        "ollama",
    )

    def __init__(self) -> None:
        self.last_selection: dict[str, Any] | None = None

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def select(
        self,
        *,
        goal: Any = None,
        plan: Any = None,
        decision: Any = None,
        result: Any = None,
    ) -> dict[str, Any]:
        """
        Select a tool without executing it.
        """

        text_parts = [
            self._text(goal),
            self._text(plan),
            self._text(decision),
            self._text(result),
        ]

        text = " ".join(part for part in text_parts if part)

        selection = self._select_from_text(text)

        self.last_selection = selection.to_dict()
        return dict(self.last_selection)

    def _select_from_text(self, text: str) -> ToolSelection:
        # --------------------------------------------------------
        # Memory
        # --------------------------------------------------------
        memory_terms = (
            "nhớ",
            "ghi nhớ",
            "lưu lại",
            "đã nhớ",
            "memory",
            "remember",
            "forget",
            "quên",
        )

        if any(term in text for term in memory_terms):
            return ToolSelection(
                tool="memory",
                reason="Request indicates memory operation.",
                confidence=0.95,
                allowed=True,
            )

        # --------------------------------------------------------
        # Time
        # --------------------------------------------------------
        time_terms = (
            "mấy giờ",
            "giờ hiện tại",
            "bây giờ là mấy giờ",
            "what time",
            "current time",
        )

        if any(term in text for term in time_terms):
            return ToolSelection(
                tool="time",
                reason="Request requires current time.",
                confidence=0.98,
                allowed=True,
            )

        # --------------------------------------------------------
        # Date
        # --------------------------------------------------------
        date_terms = (
            "hôm nay",
            "ngày bao nhiêu",
            "ngày hôm nay",
            "today",
            "current date",
        )

        if any(term in text for term in date_terms):
            return ToolSelection(
                tool="date",
                reason="Request requires current date.",
                confidence=0.98,
                allowed=True,
            )

        # --------------------------------------------------------
        # Web context
        # --------------------------------------------------------
        context_terms = (
            "tìm hiểu",
            "giải thích thông tin trên web",
            "bối cảnh trên mạng",
            "web context",
            "research",
            "nghiên cứu",
        )

        if any(term in text for term in context_terms):
            return ToolSelection(
                tool="web_context",
                reason="Request requires web context/research.",
                confidence=0.90,
                allowed=True,
            )

        # --------------------------------------------------------
        # Web
        # --------------------------------------------------------
        web_terms = (
            "tìm trên mạng",
            "tìm trên web",
            "google",
            "website",
            "trang web",
            "tin tức",
            "giá",
            "mua",
            "tìm kiếm",
            "search",
            "latest",
            "news",
        )

        if any(term in text for term in web_terms):
            return ToolSelection(
                tool="web",
                reason="Request indicates external web information.",
                confidence=0.90,
                allowed=True,
            )

        # --------------------------------------------------------
        # Action
        # --------------------------------------------------------
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
            "action",
        )

        if any(term in text for term in action_terms):
            return ToolSelection(
                tool="action",
                reason="Request indicates an executable local action.",
                confidence=0.82,
                allowed=True,
            )

        # --------------------------------------------------------
        # Ollama / reasoning fallback
        # --------------------------------------------------------
        if text:
            return ToolSelection(
                tool="ollama",
                reason="No specialized tool matched; reasoning fallback selected.",
                confidence=0.55,
                allowed=True,
            )

        # --------------------------------------------------------
        # Unknown
        # --------------------------------------------------------
        return ToolSelection(
            tool=None,
            reason="Insufficient information to select a tool.",
            confidence=0.0,
            allowed=False,
        )


def create_tool_selector() -> ToolSelector:
    return ToolSelector()
'''
    SELECTOR.write_text(selector, encoding="utf-8")
    compile_file(SELECTOR)


def find_class(tree: ast.AST, name: str) -> ast.ClassDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    fail(f"CLASS NOT FOUND: {name}")


def find_method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
    fail(f"METHOD NOT FOUND: {name}")


def patch_main() -> None:
    source = MAIN.read_text(encoding="utf-8-sig")

    if "from tool_selector import create_tool_selector" not in source:
        marker = "from __future__ import annotations"

        if marker not in source:
            fail("FUTURE IMPORT ANCHOR NOT FOUND")

        source = source.replace(
            marker,
            marker
            + "\n\n"
            + "from tool_selector import create_tool_selector",
            1,
        )

    tree = ast.parse(source, filename=str(MAIN))
    core = find_class(tree, "MinhMiniCore")

    init = find_method(core, "__init__")
    process = find_method(core, "process")

    # ------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------
    init_source = ast.get_source_segment(source, init) or ""

    if "self.tool_selector" not in init_source:
        init_marker = "self.last_p10_evaluation = None"

        if init_marker not in init_source:
            fail(
                "P11 INIT ANCHOR NOT FOUND: "
                "self.last_p10_evaluation = None"
            )

        replacement = (
            init_marker
            + "\n\n"
            + "        # P11 TOOL SELECTOR — SELECT ONLY\n"
            + "        self.tool_selector = create_tool_selector()"
        )

        source = source.replace(
            init_marker,
            replacement,
            1,
        )

    # ------------------------------------------------------------
    # PROCESS
    # ------------------------------------------------------------
    tree = ast.parse(source, filename=str(MAIN))
    core = find_class(tree, "MinhMiniCore")
    process = find_method(core, "process")

    process_source = ast.get_source_segment(source, process) or ""

    if "self.tool_selector.select(" not in process_source:
        # Insert immediately before the existing P10 evaluation hook.
        p10_anchor = "self._p10_4_run_evaluation("

        if p10_anchor not in process_source:
            fail(
                "P11 PROCESS ANCHOR NOT FOUND: "
                "self._p10_4_run_evaluation("
            )

        p11_block = """        # P11 TOOL SELECTOR — ADVISORY ONLY
        _p11_tool_selection = self.tool_selector.select(
            goal=_p10_goal,
            plan=_p10_plan,
            decision=None,
            result=_p10_result,
        )
        self.last_p11_tool_selection = _p11_tool_selection

"""

        source = source.replace(
            "        self._p10_4_run_evaluation(",
            p11_block + "        self._p10_4_run_evaluation(",
            1,
        )

    # ------------------------------------------------------------
    # STATUS STATE
    # ------------------------------------------------------------
    if "self.last_p11_tool_selection" not in source:
        marker = "self.last_p10_evaluation = None"

        source = source.replace(
            marker,
            marker
            + "\n"
            + "        self.last_p11_tool_selection = None",
            1,
        )

    # ------------------------------------------------------------
    # GUARDS
    # ------------------------------------------------------------
    forbidden = (
        "self.tool_selector.execute(",
        "self.tool_selector.run(",
        "self.tool_selector.call(",
    )

    for forbidden_call in forbidden:
        if forbidden_call in source:
            fail(f"P11 EXECUTION BYPASS DETECTED: {forbidden_call}")

    MAIN.write_text(source, encoding="utf-8")

    compile_file(MAIN)

    tree = parse_file(MAIN)
    core = find_class(tree, "MinhMiniCore")

    init = find_method(core, "__init__")
    process = find_method(core, "process")

    init_source = ast.get_source_segment(source, init) or ""
    process_source = ast.get_source_segment(source, process) or ""

    if "self.tool_selector" not in init_source:
        fail("P11 INIT VALIDATION FAILED")

    if "self.tool_selector.select(" not in process_source:
        fail("P11 PROCESS VALIDATION FAILED")

    if "self.last_p11_tool_selection" not in source:
        fail("P11 STATE VALIDATION FAILED")


def main() -> int:
    print("=" * 60)
    print("P11-1 TOOL SELECTOR INTEGRATION")
    print("=" * 60)

    if not MAIN.exists():
        fail("main.py NOT FOUND")

    print("MAIN FILE: PASS")

    compile_file(MAIN)
    print("MAIN PRECOMPILE: PASS")

    write_selector()
    print("TOOL_SELECTOR MODULE: PASS")

    if BACKUP.exists():
        BACKUP.unlink()

    shutil.copy2(MAIN, BACKUP)
    print("BACKUP CREATED:", BACKUP.name)

    try:
        patch_main()
        print("MAIN.PY PATCH: PASS")
        print("FINAL COMPILE: PASS")

        import importlib

        if "main" in sys.modules:
            del sys.modules["main"]

        main_module = importlib.import_module("main")
        print("MAIN IMPORT: PASS")

        core = getattr(main_module, "MINH", None)

        if core is None:
            fail("GLOBAL MINH NOT FOUND")

        print("GLOBAL MINH: PASS")

        selector = getattr(core, "tool_selector", None)

        if selector is None:
            fail("MINH.tool_selector NOT FOUND")

        print("MINH.tool_selector: PASS")

        selection = selector.select(
            goal="tìm giá iphone mới nhất",
            plan=None,
            decision=None,
            result=None,
        )

        if not isinstance(selection, dict):
            fail("TOOL SELECTOR DID NOT RETURN DICT")

        if selection.get("tool") != "web":
            fail(
                "TOOL SELECTOR TEST FAILED: "
                f"expected web, got {selection.get('tool')!r}"
            )

        print("DIRECT TOOL SELECTION: PASS")
        print("SELECTED TOOL:", selection.get("tool"))
        print("CONFIDENCE:", selection.get("confidence"))

        if selection.get("advisory_only") is not True:
            fail("ADVISORY-ONLY FLAG FAILED")

        print("ADVISORY-ONLY: PASS")

        print()
        print("=" * 60)
        print("P11-1 RESULT: PASS")
        print("TOOL SELECTOR: INTEGRATED")
        print("EXECUTION: UNCHANGED")
        print("P11 MODE: SELECT ONLY")
        print("=" * 60)

        return 0

    except Exception as exc:
        print()
        print("P11-1 FAILED — ROLLBACK")

        if BACKUP.exists():
            shutil.copy2(BACKUP, MAIN)
            print("ROLLBACK: PASS")

        print("ERROR:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
