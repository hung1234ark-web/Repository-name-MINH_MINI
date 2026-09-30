# ============================================================
# MINH MINI — FINAL REPAIR 03
# EXECUTION CONTROLLER HANDLER COMPATIBILITY
# ============================================================

from pathlib import Path
import sys
import inspect
import importlib
import traceback


APP_DIR = Path(r"C:\Users\Admin\MINH_MINI\app")

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# FAKE HANDLERS
# ============================================================

def fake_action(
    message="",
    **kwargs,
):
    return {
        "success": True,
        "response": (
            "[FAKE ACTION] "
            + str(kwargs.get("action", ""))
            + " "
            + str(kwargs.get("target", ""))
        ),
        "intent": "action",
        "tool": "action",
        "action": kwargs.get("action", ""),
        "target": kwargs.get("target", ""),
    }


def fake_web(
    message="",
    **kwargs,
):
    return {
        "success": True,
        "response": "[FAKE WEB] Đã tìm kiếm.",
        "intent": "web",
        "tool": "web",
        "query": kwargs.get("query", ""),
    }


def fake_chat(
    message="",
    **kwargs,
):
    return {
        "success": True,
        "response": "[FAKE CHAT] Xin chào Lam!",
        "intent": "chat",
        "tool": "ollama",
    }


# ============================================================
# IMPORT
# ============================================================

import brain
import router_guard
import execution_controller


importlib.reload(
    execution_controller
)


# ============================================================
# SIGNATURE DIAGNOSTIC
# ============================================================

def show_signature(name, handler):

    print()
    print(f"--- {name} ---")

    try:
        print(
            "signature:",
            inspect.signature(handler),
        )

    except Exception as exc:
        print(
            "signature error:",
            exc,
        )


# ============================================================
# RAW CONTROLLER TEST
# ============================================================

def test_controller():

    print("=" * 60)
    print(
        "MINH MINI — REPAIR 03"
    )
    print(
        "EXECUTION CONTROLLER DIAGNOSTIC"
    )
    print("=" * 60)

    handlers = {
        "action": fake_action,
        "web": fake_web,
        "ollama": fake_chat,
        "chat": fake_chat,
    }

    for name, handler in handlers.items():
        show_signature(
            name,
            handler,
        )

    print()
    print(
        "Creating controller..."
    )

    try:

        controller = (
            execution_controller
            .ExecutionController(
                handlers=handlers,
            )
        )

        print(
            "[PASS] controller created"
        )

    except Exception as exc:

        print(
            "[FAIL] controller create"
        )
        print(exc)

        traceback.print_exc()

        return

    # --------------------------------------------------------
    # DIRECT HANDLER TEST
    # --------------------------------------------------------

    print()
    print(
        "=== DIRECT HANDLER TEST ==="
    )

    try:

        result = fake_action(
            message="mở Google",
            action="open",
            target="google",
        )

        print(
            "[PASS] fake_action direct"
        )

        print(
            "result:",
            result,
        )

    except Exception as exc:

        print(
            "[FAIL] fake_action direct"
        )
        print(exc)

    # --------------------------------------------------------
    # CONTROLLER HANDLER REGISTRATION
    # --------------------------------------------------------

    print()
    print(
        "=== REGISTERED HANDLERS ==="
    )

    try:

        for name in (
            "action",
            "web",
            "ollama",
            "chat",
        ):

            handler = (
                controller.get_handler(
                    name
                )
            )

            print(
                name,
                "=>",
                handler,
            )

            if callable(handler):
                print(
                    "  [PASS] callable"
                )

                show_signature(
                    name,
                    handler,
                )

            else:
                print(
                    "  [FAIL] not callable"
                )

    except Exception as exc:

        print(
            "[FAIL] handler inspection"
        )

        print(exc)

    # --------------------------------------------------------
    # BRAIN → ROUTER → CONTROLLER
    # --------------------------------------------------------

    print()
    print(
        "=== BRAIN → ROUTER → CONTROLLER ==="
    )

    cases = [
        "mở Google",
        "tìm trên web giá iPhone",
        "xin chào",
    ]

    for message in cases:

        print()
        print(
            "MESSAGE:",
            message,
        )

        try:

            decision = brain.think(
                message
            )

            print(
                "brain intent:",
                getattr(
                    decision,
                    "intent",
                    "",
                ),
            )

            route = (
                router_guard
                .validate_route(
                    message,
                    decision,
                )
            )

            print(
                "route intent:",
                getattr(
                    route,
                    "intent",
                    "",
                ),
            )

            print(
                "route tool:",
                getattr(
                    route,
                    "tool",
                    "",
                ),
            )

            print(
                "route action:",
                getattr(
                    route,
                    "action",
                    "",
                ),
            )

            print(
                "route target:",
                getattr(
                    route,
                    "target",
                    "",
                ),
            )

            print()
            print(
                "EXECUTING..."
            )

            result = controller.execute(
                message,
                route,
            )

            print(
                "result type:",
                type(result),
            )

            print(
                "success:",
                getattr(
                    result,
                    "success",
                    None,
                ),
            )

            print(
                "response:",
                repr(
                    getattr(
                        result,
                        "response",
                        None,
                    )
                ),
            )

            print(
                "intent:",
                getattr(
                    result,
                    "intent",
                    None,
                ),
            )

            print(
                "tool:",
                getattr(
                    result,
                    "tool",
                    None,
                ),
            )

            print(
                "action:",
                getattr(
                    result,
                    "action",
                    None,
                ),
            )

            print(
                "target:",
                getattr(
                    result,
                    "target",
                    None,
                ),
            )

        except Exception as exc:

            print(
                "[FAIL] execution"
            )

            print(
                "error:",
                exc,
            )

            traceback.print_exc()

    # --------------------------------------------------------
    # INTERNAL CALL METHOD
    # --------------------------------------------------------

    print()
    print(
        "=== INTERNAL _CALL_HANDLER ==="
    )

    try:

        result = controller._call_handler(
            fake_action,
            "mở Google",
            intent="action",
            tool="action",
            action="open",
            target="google",
            query="",
            reference="",
            source_number=None,
            decision={
                "intent": "action",
                "tool": "action",
                "action": "open",
                "target": "google",
            },
        )

        print(
            "raw _call_handler result:"
        )

        print(
            repr(result)
        )

        if isinstance(
            result,
            dict,
        ):

            print(
                "[PASS] returned dict"
            )

            print(
                "success =",
                result.get(
                    "success"
                ),
            )

            print(
                "response =",
                repr(
                    result.get(
                        "response"
                    )
                ),
            )

        else:

            print(
                "[WARN] result is not dict"
            )

    except Exception as exc:

        print(
            "[FAIL] _call_handler"
        )

        print(exc)

        traceback.print_exc()

    print()
    print("=" * 60)
    print(
        "REPAIR 03 DIAGNOSTIC HOÀN TẤT"
    )
    print("=" * 60)


if __name__ == "__main__":
    test_controller()