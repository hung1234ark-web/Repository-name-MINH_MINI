

"""
MINH MINI — REAL HANDLER SMOKE TEST
Bản sửa:
- Gọi handle_action_command đúng contract.
- Truyền command/message/decision/action/target/query khi handler hỗ trợ.
- Không sửa action.py.
"""

from __future__ import annotations

import importlib
import inspect
import sys
import time
from pathlib import Path
from typing import Any, Callable


APP_DIR = Path(__file__).resolve().parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


TOTAL = 0
PASS = 0
FAIL = 0
SKIP = 0


def report(name: str, status: str, detail: str = "") -> None:
    global TOTAL, PASS, FAIL, SKIP

    TOTAL += 1

    if status == "PASS":
        PASS += 1
        mark = "[PASS]"
    elif status == "SKIP":
        SKIP += 1
        mark = "[SKIP]"
    else:
        FAIL += 1
        mark = "[FAIL]"

    print(f"{mark} {name}")

    if detail:
        print(f"       {detail}")


def safe_import(module_name: str):
    try:
        module = importlib.import_module(module_name)
        report(f"import:{module_name}", "PASS")
        return module
    except Exception as exc:
        report(
            f"import:{module_name}",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )
        return None


def find_callable(module: Any, names: list[str]):
    for name in names:
        obj = getattr(module, name, None)

        if callable(obj):
            return name, obj

    return None


def decision_value(decision: Any, name: str, default: str = "") -> str:
    value = getattr(decision, name, default)

    if value is None:
        return default

    return str(value)


def call_handler(
    handler: Callable,
    *,
    message: str = "",
    command: str = "",
    decision: Any = None,
) -> Any:
    """
    Gọi handler theo đúng signature thực tế.

    Ưu tiên truyền:
    command
    message
    decision
    action
    target
    query

    Chỉ truyền những tham số mà handler hỗ trợ.
    """

    sig = inspect.signature(handler)
    params = sig.parameters

    values = {
        "command": command or message,
        "message": message or command,
        "decision": decision,
        "action": decision_value(decision, "action"),
        "target": decision_value(decision, "target"),
        "query": decision_value(decision, "query"),
    }

    kwargs = {}

    accepts_var_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in params.values()
    )

    for name, value in values.items():

        if name in params:
            kwargs[name] = value

        elif accepts_var_kwargs and name in {
            "action",
            "target",
            "query",
        }:
            kwargs[name] = value

    # Nếu handler có command là tham số bắt buộc,
    # đảm bảo command luôn được truyền.
    if "command" in params:
        command_param = params["command"]

        if (
            command_param.default is inspect.Parameter.empty
            and "command" not in kwargs
        ):
            kwargs["command"] = command or message

    return handler(**kwargs)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in (
            "response",
            "answer",
            "text",
            "message",
            "result",
            "output",
        ):
            item = value.get(key)

            if isinstance(item, str) and item.strip():
                return item.strip()

        return str(value).strip()

    for attr in (
        "response",
        "answer",
        "text",
        "message",
        "result",
        "output",
    ):
        item = getattr(value, attr, None)

        if isinstance(item, str) and item.strip():
            return item.strip()

    return str(value).strip()


print()
print("=" * 70)
print("MINH MINI — REAL HANDLER SMOKE TEST")
print("=" * 70)
print()


# ============================================================
# IMPORT
# ============================================================

brain = safe_import("brain")
router = safe_import("router_guard")
controller_mod = safe_import("execution_controller")
response_guard = safe_import("response_guard")
action = safe_import("action")
web = safe_import("web")
web_ai = safe_import("web_ai")


# ============================================================
# BRAIN
# ============================================================

brain_obj = None
decision = None

if brain is not None:
    try:
        BrainCore = getattr(brain, "BrainCore", None)

        if BrainCore is None:
            raise AttributeError("Không tìm thấy BrainCore")

        brain_obj = BrainCore()

        if not hasattr(brain_obj, "think"):
            raise AttributeError("BrainCore không có think()")

        decision = brain_obj.think("mở Google")

        if decision is not None:
            report(
                "brain:real_decision",
                "PASS",
                f"{type(decision).__name__}: {decision}",
            )
        else:
            report(
                "brain:real_decision",
                "FAIL",
                "think() trả None",
            )

    except Exception as exc:
        report(
            "brain:real_decision",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# ROUTER
# ============================================================

routed_decision = decision

if router is not None and decision is not None:

    validate_route = getattr(
        router,
        "validate_route",
        None,
    )

    if callable(validate_route):

        try:
            routed_decision = validate_route(
                "mở Google",
                decision,
            )

            report(
                "router:real_route",
                "PASS",
                str(routed_decision),
            )

        except Exception as exc:
            report(
                "router:real_route",
                "FAIL",
                f"{type(exc).__name__}: {exc}",
            )

    else:
        report(
            "router:real_route",
            "FAIL",
            "Không tìm thấy validate_route()",
        )


# ============================================================
# DISCOVER ACTION
# ============================================================

action_handler = None

if action is not None:

    found = find_callable(
        action,
        [
            "handle_action_command",
            "handle_action",
            "execute_action",
            "run_action",
        ],
    )

    if found:

        name, action_handler = found

        report(
            "discover:action_handler",
            "PASS",
            name,
        )

    else:

        report(
            "discover:action_handler",
            "FAIL",
            "Không tìm thấy action handler.",
        )


# ============================================================
# DISCOVER WEB
# ============================================================

web_handler = None

if web is not None:

    found = find_callable(
        web,
        [
            "safe_search",
            "search_web",
            "web_search",
            "search",
        ],
    )

    if found:

        name, web_handler = found

        report(
            "discover:web_handler",
            "PASS",
            name,
        )

    else:

        report(
            "discover:web_handler",
            "FAIL",
            "Không tìm thấy web handler.",
        )


# ============================================================
# DISCOVER CHAT
# ============================================================

chat_handler = None

for module_name, module in (
    ("web_ai", web_ai),
    ("brain", brain),
):

    if chat_handler is not None:
        break

    if module is None:
        continue

    found = find_callable(
        module,
        [
            "chat",
            "ask",
            "ollama_chat",
            "query_ollama",
            "ask_ollama",
            "generate_response",
        ],
    )

    if found:

        name, chat_handler = found

        report(
            f"discover:chat_handler:{module_name}",
            "PASS",
            name,
        )


# ============================================================
# REAL ACTION
# ============================================================

print()
print("--- REAL ACTION TEST ---")

if action_handler is None:

    report(
        "real_action:mở Google",
        "SKIP",
        "Không có action handler.",
    )

else:

    try:

        started = time.perf_counter()

        result = call_handler(
            action_handler,
            message="mở Google",
            command="mở Google",
            decision=routed_decision,
        )

        elapsed = time.perf_counter() - started

        text = normalize_text(result)

        if text:

            report(
                "real_action:mở Google",
                "PASS",
                f"{text!r} | {elapsed:.2f}s",
            )

        else:

            report(
                "real_action:mở Google",
                "FAIL",
                f"Handler trả kết quả rỗng | {elapsed:.2f}s",
            )

    except Exception as exc:

        report(
            "real_action:mở Google",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# REAL WEB
# ============================================================

print()
print("--- REAL WEB TEST ---")

if web_handler is None:

    report(
        "real_web:tìm giá iPhone",
        "SKIP",
        "Không có web handler.",
    )

else:

    try:

        started = time.perf_counter()

        result = call_handler(
            web_handler,
            message="giá iPhone mới nhất",
            command="giá iPhone mới nhất",
            decision=None,
        )

        elapsed = time.perf_counter() - started

        text = normalize_text(result)

        if text:

            report(
                "real_web:tìm giá iPhone",
                "PASS",
                f"{text[:500]!r} | {elapsed:.2f}s",
            )

        else:

            report(
                "real_web:tìm giá iPhone",
                "FAIL",
                f"Web handler trả rỗng | {elapsed:.2f}s",
            )

    except Exception as exc:

        report(
            "real_web:tìm giá iPhone",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# REAL CHAT
# ============================================================

print()
print("--- REAL CHAT / OLLAMA TEST ---")

if chat_handler is None:

    report(
        "real_chat:Ollama",
        "SKIP",
        "Chưa tìm thấy chat/Ollama handler.",
    )

else:

    try:

        started = time.perf_counter()

        result = call_handler(
            chat_handler,
            message="Xin chào Lam, trả lời thật ngắn.",
            command="Xin chào Lam, trả lời thật ngắn.",
            decision=None,
        )

        elapsed = time.perf_counter() - started

        text = normalize_text(result)

        if text:

            report(
                "real_chat:Ollama",
                "PASS",
                f"{text[:500]!r} | {elapsed:.2f}s",
            )

        else:

            report(
                "real_chat:Ollama",
                "FAIL",
                f"Chat handler trả rỗng | {elapsed:.2f}s",
            )

    except Exception as exc:

        report(
            "real_chat:Ollama",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# RESPONSE GUARD
# ============================================================

if response_guard is not None:

    try:

        validate_response = getattr(
            response_guard,
            "validate_response",
            None,
        )

        if not callable(validate_response):
            raise AttributeError(
                "Không tìm thấy response_guard.validate_response()"
            )

        result = validate_response(
            "xin chào",
            "MINH MINI đang hoạt động.",
            decision=decision,
            execution_result=None,
        )

        valid = False

        if isinstance(result, tuple):

            valid = bool(result[0])

        elif isinstance(result, dict):

            valid = bool(
                result.get("valid")
                or result.get("ok")
                or result.get("success")
            )

        else:

            valid = bool(
                getattr(result, "valid", False)
                or getattr(result, "ok", False)
                or getattr(result, "success", False)
            )

        if valid:

            report(
                "response_guard:real_output",
                "PASS",
                str(result),
            )

        else:

            report(
                "response_guard:real_output",
                "FAIL",
                str(result),
            )

    except Exception as exc:

        report(
            "response_guard:real_output",
            "FAIL",
            f"{type(exc).__name__}: {exc}",
        )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("REAL HANDLER TEST SUMMARY")
print("=" * 70)

print(f"TOTAL : {TOTAL}")
print(f"PASS  : {PASS}")
print(f"FAIL  : {FAIL}")
print(f"SKIP  : {SKIP}")

print()

if FAIL == 0:

    print(">>> REAL HANDLER SMOKE TEST: PASS")

else:

    print(">>> REAL HANDLER SMOKE TEST: FAIL")
    print(">>> Dùng lỗi thực tế để xác định ROOT CAUSE.")

print("=" * 70)
