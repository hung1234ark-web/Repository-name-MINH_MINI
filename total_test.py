# ============================================================
# MINH MINI — TOTAL TEST FINAL
# Kiểm thử tổng thể kiến trúc MINH MINI
# Không tự ý mở ứng dụng thật trong quá trình test
# ============================================================

from __future__ import annotations

import ast
import importlib
import sys
import traceback
from pathlib import Path


# ============================================================
# PATH
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent


# ============================================================
# MODULES
# ============================================================

MODULES = [
    "brain",
    "conversation_state",
    "execution_controller",
    "router_guard",
    "response_guard",
    "app_bridge",
    "action",
    "web_context",
    "web",
    "web_ai",
    "command_completion",
    "main",
]


# ============================================================
# TEST RESULT
# ============================================================

class TestResult:

    def __init__(
        self,
        name: str,
        passed: bool,
        detail: str = "",
    ):

        self.name = name
        self.passed = passed
        self.detail = detail


RESULTS: list[TestResult] = []


def record(
    name: str,
    passed: bool,
    detail: str = "",
) -> None:

    RESULTS.append(
        TestResult(
            name,
            passed,
            detail,
        )
    )

    status = "PASS" if passed else "FAIL"

    print(
        f"[{status}] {name}"
    )

    if detail:
        print(
            f"       {detail}"
        )


# ============================================================
# TEST 1 — FILE EXISTENCE
# ============================================================

def test_files() -> None:

    print()
    print("=== 01. FILE EXISTENCE ===")

    required = [
        "brain.py",
        "conversation_state.py",
        "execution_controller.py",
        "router_guard.py",
        "response_guard.py",
        "app_bridge.py",
        "action.py",
        "web_context.py",
        "web.py",
        "web_ai.py",
        "command_completion.py",
        "main.py",
    ]

    for filename in required:

        path = APP_DIR / filename

        record(
            f"file:{filename}",
            path.exists(),
            str(path),
        )


# ============================================================
# TEST 2 — SYNTAX
# ============================================================

def test_syntax() -> None:

    print()
    print("=== 02. PYTHON SYNTAX ===")

    for filename in MODULES:

        path = APP_DIR / f"{filename}.py"

        if not path.exists():

            record(
                f"syntax:{filename}",
                False,
                "File không tồn tại.",
            )

            continue

        try:

            source = path.read_text(
                encoding="utf-8"
            )

            ast.parse(
                source,
                filename=str(path),
            )

            record(
                f"syntax:{filename}",
                True,
            )

        except Exception as exc:

            record(
                f"syntax:{filename}",
                False,
                str(exc),
            )


# ============================================================
# TEST 3 — IMPORT
# ============================================================

def test_imports() -> dict[str, object]:

    print()
    print("=== 03. MODULE IMPORT ===")

    imported = {}

    if str(APP_DIR) not in sys.path:

        sys.path.insert(
            0,
            str(APP_DIR),
        )

    for name in MODULES:

        try:

            module = importlib.import_module(
                name
            )

            imported[name] = module

            record(
                f"import:{name}",
                True,
            )

        except Exception as exc:

            imported[name] = None

            record(
                f"import:{name}",
                False,
                f"{type(exc).__name__}: {exc}",
            )

    return imported


# ============================================================
# TEST 4 — MODULE SELF CHECK
# ============================================================

def test_self_checks(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 04. MODULE SELF CHECK ===")

    for name in MODULES:

        module = imported.get(
            name
        )

        if module is None:

            record(
                f"selfcheck:{name}",
                False,
                "Module import thất bại.",
            )

            continue

        checker = getattr(
            module,
            "_self_check",
            None,
        )

        if checker is None:

            checker = getattr(
                module,
                "self_check",
                None,
            )

        if checker is None:

            record(
                f"selfcheck:{name}",
                True,
                "Không có self-check riêng.",
            )

            continue

        try:

            result = checker()

            if isinstance(
                result,
                dict,
            ):

                failed = [
                    key
                    for key, value
                    in result.items()
                    if not bool(value)
                ]

                if failed:

                    record(
                        f"selfcheck:{name}",
                        False,
                        "FAIL: "
                        + ", ".join(failed),
                    )

                else:

                    record(
                        f"selfcheck:{name}",
                        True,
                        f"{len(result)} checks.",
                    )

            else:

                record(
                    f"selfcheck:{name}",
                    bool(result),
                    str(result),
                )

        except Exception as exc:

            record(
                f"selfcheck:{name}",
                False,
                f"{type(exc).__name__}: {exc}",
            )


# ============================================================
# TEST 5 — BRAIN
# ============================================================

def test_brain(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 05. BRAIN ===")

    brain = imported.get(
        "brain"
    )

    if brain is None:

        record(
            "brain_available",
            False,
        )

        return

    think = getattr(
        brain,
        "think",
        None,
    )

    if not callable(think):

        record(
            "brain_think",
            False,
            "Không có think().",
        )

        return

    samples = [
        "mấy giờ rồi",
        "hôm nay là ngày bao nhiêu",
        "mở google",
        "tìm trên web iphone mới nhất",
        "nhớ Lam đang học Python",
        "Lam là ai",
    ]

    for index, text in enumerate(
        samples,
        start=1,
    ):

        try:

            decision = think(
                text
            )

            intent = getattr(
                decision,
                "intent",
                "",
            )

            record(
                f"brain_case_{index}",
                bool(decision),
                f"intent={intent}",
            )

        except Exception as exc:

            record(
                f"brain_case_{index}",
                False,
                str(exc),
            )


# ============================================================
# TEST 6 — ROUTER GUARD
# ============================================================

def test_router_guard(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 06. ROUTER GUARD ===")

    router = imported.get(
        "router_guard"
    )

    if router is None:

        record(
            "router_available",
            False,
        )

        return

    validator = getattr(
        router,
        "validate_route",
        None,
    )

    if not callable(
        validator
    ):

        record(
            "router_validate_route",
            False,
            "Không có validate_route().",
        )

        return

    cases = [
        (
            "mấy giờ rồi",
            "time",
        ),
        (
            "hôm nay ngày mấy",
            "date",
        ),
        (
            "mở google",
            "action",
        ),
        (
            "tìm trên web iphone",
            "web",
        ),
    ]

    for index, (
        text,
        expected,
    ) in enumerate(
        cases,
        start=1,
    ):

        try:

            result = validator(
                text,
                intent=expected,
            )

            valid = getattr(
                result,
                "valid",
                False,
            )

            record(
                f"router_case_{index}",
                bool(valid),
                f"expected={expected}",
            )

        except TypeError:

            try:

                result = validator(
                    text
                )

                valid = getattr(
                    result,
                    "valid",
                    False,
                )

                record(
                    f"router_case_{index}",
                    bool(valid),
                    f"expected={expected}",
                )

            except Exception as exc:

                record(
                    f"router_case_{index}",
                    False,
                    str(exc),
                )

        except Exception as exc:

            record(
                f"router_case_{index}",
                False,
                str(exc),
            )


# ============================================================
# TEST 7 — RESPONSE GUARD
# ============================================================

def test_response_guard(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 07. RESPONSE GUARD ===")

    guard = imported.get(
        "response_guard"
    )

    if guard is None:

        record(
            "response_guard_available",
            False,
        )

        return

    validate = getattr(
        guard,
        "validate_response",
        None,
    )

    if not callable(validate):

        record(
            "response_guard_validate",
            False,
        )

        return

    # Normal answer
    try:

        result = validate(
            "Python là gì?",
            "Python là ngôn ngữ lập trình.",
        )

        record(
            "response_normal",
            bool(
                getattr(
                    result,
                    "valid",
                    False,
                )
            ),
        )

    except Exception as exc:

        record(
            "response_normal",
            False,
            str(exc),
        )

    # Empty answer
    try:

        result = validate(
            "hello",
            "",
        )

        answer = getattr(
            result,
            "answer",
            "",
        )

        record(
            "response_empty_protection",
            bool(answer),
        )

    except Exception as exc:

        record(
            "response_empty_protection",
            False,
            str(exc),
        )

    # False action claim
    try:

        result = validate(
            "mở google",
            "Đã mở Google thành công.",
            execution_result=None,
            decision={
                "intent": "action",
                "tool": "action",
            },
        )

        answer = str(
            getattr(
                result,
                "answer",
                "",
            )
        ).lower()

        record(
            "response_action_protection",
            "chưa" in answer,
        )

    except Exception as exc:

        record(
            "response_action_protection",
            False,
            str(exc),
        )


# ============================================================
# TEST 8 — APP BRIDGE SAFE BEHAVIOR
# ============================================================

def test_app_bridge(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 08. APP BRIDGE ===")

    bridge = imported.get(
        "app_bridge"
    )

    if bridge is None:

        record(
            "bridge_available",
            False,
        )

        return

    resolve = getattr(
        bridge,
        "resolve_target",
        None,
    )

    if callable(resolve):

        try:

            key, info = resolve(
                "youtube"
            )

            record(
                "bridge_alias_youtube",
                key == "youtube"
                and info is not None,
            )

        except Exception as exc:

            record(
                "bridge_alias_youtube",
                False,
                str(exc),
            )

    # QUAN TRỌNG:
    # test target giả, không mở ứng dụng thật.
    open_target = getattr(
        bridge,
        "open_target",
        None,
    )

    if callable(open_target):

        try:

            result = open_target(
                "__MINH_MINI_TEST_UNKNOWN__"
            )

            success = getattr(
                result,
                "success",
                True,
            )

            error = getattr(
                result,
                "error",
                "",
            )

            record(
                "bridge_unknown_target_safe",
                success is False
                and bool(error),
            )

        except Exception as exc:

            record(
                "bridge_unknown_target_safe",
                False,
                str(exc),
            )


# ============================================================
# TEST 9 — EXECUTION CONTROLLER
# ============================================================

def test_execution_controller(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 09. EXECUTION CONTROLLER ===")

    controller_module = imported.get(
        "execution_controller"
    )

    if controller_module is None:

        record(
            "controller_available",
            False,
        )

        return

    Controller = getattr(
        controller_module,
        "ExecutionController",
        None,
    )

    if Controller is None:

        record(
            "controller_class",
            False,
        )

        return

    try:

        def test_handler(
            message="",
            **kwargs,
        ):

            return {
                "success": True,
                "response": "TEST_OK",
            }

        controller = Controller(
            handlers={
                "chat": test_handler,
            }
        )

        result = controller.execute(
            {
                "intent": "chat",
                "tool": "chat",
                "action": "",
                "target": "",
                "query": "",
            },
            message="test",
        )

        success = getattr(
            result,
            "success",
            False,
        )

        record(
            "controller_dispatch",
            bool(success),
        )

    except Exception as exc:

        record(
            "controller_dispatch",
            False,
            str(exc),
        )


# ============================================================
# TEST 10 — WEB CONTEXT
# ============================================================

def test_web_context(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 10. WEB CONTEXT ===")

    module = imported.get(
        "web_context"
    )

    if module is None:

        record(
            "web_context_available",
            False,
        )

        return

    try:

        cls = getattr(
            module,
            "WebSource",
            None,
        )

        if cls is None:

            record(
                "web_source_class",
                False,
            )

            return

        source = cls(
            number=1,
            title="Test Source",
            url="https://example.com",
            snippet="Test",
        )

        record(
            "web_source_create",
            source.number == 1
            and source.title == "Test Source",
        )

    except Exception as exc:

        record(
            "web_source_create",
            False,
            str(exc),
        )


# ============================================================
# TEST 11 — MAIN IMPORT
# ============================================================

def test_main_import(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 11. MAIN ORCHESTRATOR ===")

    main = imported.get(
        "main"
    )

    if main is None:

        record(
            "main_import",
            False,
        )

        return

    record(
        "main_import",
        True,
    )

    for name in (
        "process",
        "ask",
        "chat",
        "status",
        "self_check",
    ):

        value = getattr(
            main,
            name,
            None,
        )

        record(
            f"main_api:{name}",
            callable(value),
        )


# ============================================================
# TEST 12 — MAIN SELF CHECK
# ============================================================

def test_main_self_check(
    imported: dict[str, object],
) -> None:

    print()
    print("=== 12. MAIN SELF CHECK ===")

    main = imported.get(
        "main"
    )

    if main is None:

        record(
            "main_self_check",
            False,
        )

        return

    checker = getattr(
        main,
        "self_check",
        None,
    )

    if not callable(checker):

        record(
            "main_self_check",
            False,
            "Không có self_check().",
        )

        return

    try:

        result = checker()

        if isinstance(
            result,
            dict,
        ):

            failed = [
                key
                for key, value
                in result.items()
                if not bool(value)
            ]

            record(
                "main_self_check",
                not failed,
                (
                    "FAIL: "
                    + ", ".join(failed)
                    if failed
                    else f"{len(result)} checks."
                ),
            )

        else:

            record(
                "main_self_check",
                bool(result),
                str(result),
            )

    except Exception as exc:

        record(
            "main_self_check",
            False,
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# SUMMARY
# ============================================================

def print_summary() -> None:

    print()
    print("=" * 60)
    print("MINH MINI — TOTAL TEST FINAL")
    print("=" * 60)

    total = len(
        RESULTS
    )

    passed = sum(
        1
        for item in RESULTS
        if item.passed
    )

    failed = total - passed

    print(
        f"TOTAL : {total}"
    )

    print(
        f"PASS  : {passed}"
    )

    print(
        f"FAIL  : {failed}"
    )

    if failed == 0:

        print()
        print(
            ">>> TOTAL TEST: PASS"
        )

    else:

        print()
        print(
            ">>> TOTAL TEST: CÓ LỖI CẦN SỬA"
        )

        print()
        print(
            "Danh sách FAIL:"
        )

        for item in RESULTS:

            if not item.passed:

                print(
                    f"- {item.name}: "
                    f"{item.detail}"
                )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    print()
    print("=" * 60)
    print("MINH MINI — FINAL TOTAL INTEGRATION TEST")
    print("=" * 60)
    print(
        f"APP : {APP_DIR}"
    )
    print(
        f"ROOT: {PROJECT_DIR}"
    )
    print()

    test_files()

    test_syntax()

    imported = test_imports()

    test_self_checks(
        imported
    )

    test_brain(
        imported
    )

    test_router_guard(
        imported
    )

    test_response_guard(
        imported
    )

    test_app_bridge(
        imported
    )

    test_execution_controller(
        imported
    )

    test_web_context(
        imported
    )

    test_main_import(
        imported
    )

    test_main_self_check(
        imported
    )

    print_summary()

    failed = sum(
        1
        for item in RESULTS
        if not item.passed
    )

    return (
        0
        if failed == 0
        else 1
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )