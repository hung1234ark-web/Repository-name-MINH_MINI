# ============================================================
# MINH MINI — FINAL REPAIR 02
# RESPONSE GUARD + ROUTER GUARD DIAGNOSTIC / REPAIR
# ============================================================

from pathlib import Path
import ast
import importlib
import sys
import traceback


APP_DIR = Path(r"C:\Users\Admin\MINH_MINI\app")

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# BASIC
# ============================================================

def banner(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def syntax_check(filename):
    path = APP_DIR / filename

    try:
        source = path.read_text(
            encoding="utf-8"
        )

        ast.parse(
            source,
            filename=str(path),
        )

        print(f"[PASS] syntax:{filename}")
        return True

    except Exception as exc:
        print(f"[FAIL] syntax:{filename}")
        print(f"       {exc}")
        return False


# ============================================================
# RESPONSE GUARD
# ============================================================

def test_response_guard():
    banner("01. RESPONSE GUARD — DIRECT TEST")

    try:
        import response_guard

        importlib.reload(response_guard)

    except Exception as exc:
        print("[FAIL] import response_guard")
        print(f"       {exc}")
        return False

    print()
    print("TEST A — normal answer")

    try:
        result = response_guard.validate_response(
            "hello",
            "Xin chào Lam!",
            decision={
                "intent": "chat",
                "tool": "ollama",
            },
        )

        print("valid   =", getattr(result, "valid", None))
        print("answer  =", repr(getattr(result, "answer", None)))
        print("reason  =", getattr(result, "reason", None))

    except Exception as exc:
        print("[FAIL] normal")
        print(f"       {exc}")

    print()
    print("TEST B — empty answer")

    try:
        result = response_guard.validate_response(
            "hello",
            "",
            decision={
                "intent": "chat",
                "tool": "ollama",
            },
        )

        valid = getattr(
            result,
            "valid",
            None,
        )

        answer = getattr(
            result,
            "answer",
            None,
        )

        reason = getattr(
            result,
            "reason",
            None,
        )

        print("valid   =", valid)
        print("answer  =", repr(answer))
        print("reason  =", reason)

        if valid and answer:
            print("[PASS] empty answer protection")
        else:
            print("[FAIL] empty answer protection")

    except Exception as exc:
        print("[FAIL] empty answer test")
        print(f"       {exc}")
        traceback.print_exc()

    print()
    print("TEST C — action without execution success")

    try:
        result = response_guard.validate_response(
            "mở Google",
            "Đã mở Google.",
            decision={
                "intent": "action",
                "tool": "action",
                "action": "open",
                "target": "Google",
            },
            execution_result={
                "success": False,
                "response": "Không mở được Google.",
            },
        )

        print("valid   =", getattr(result, "valid", None))
        print("answer  =", repr(getattr(result, "answer", None)))
        print("reason  =", getattr(result, "reason", None))

    except Exception as exc:
        print("[FAIL] action protection")
        print(f"       {exc}")

    print()
    print("TEST D — action with execution success")

    try:
        result = response_guard.validate_response(
            "mở Google",
            "Đã mở Google.",
            decision={
                "intent": "action",
                "tool": "action",
                "action": "open",
                "target": "Google",
            },
            execution_result={
                "success": True,
                "response": "Đã mở Google.",
            },
        )

        print("valid   =", getattr(result, "valid", None))
        print("answer  =", repr(getattr(result, "answer", None)))
        print("reason  =", getattr(result, "reason", None))

    except Exception as exc:
        print("[FAIL] successful action")
        print(f"       {exc}")

    print()
    print("SELF CHECK:")

    try:
        checks = response_guard._self_check()

        for name, ok in checks.items():
            print(
                f"[{'PASS' if ok else 'FAIL'}] "
                f"{name}"
            )

    except Exception as exc:
        print("[FAIL] response_guard self_check")
        print(f"       {exc}")

    return True


# ============================================================
# ROUTER GUARD
# ============================================================

def test_router_guard():
    banner("02. ROUTER GUARD — DIRECT TEST")

    try:
        import router_guard

        importlib.reload(router_guard)

    except Exception as exc:
        print("[FAIL] import router_guard")
        print(f"       {exc}")
        return False

    # --------------------------------------------------------
    # CASE 1
    # --------------------------------------------------------

    cases = [
        (
            "CASE 1 — time",
            "mấy giờ rồi",
            {
                "intent": "time",
                "tool": "time",
            },
        ),
        (
            "CASE 2 — date",
            "hôm nay là ngày bao nhiêu",
            {
                "intent": "date",
                "tool": "date",
            },
        ),
        (
            "CASE 3 — action",
            "mở Google",
            {
                "intent": "action",
                "tool": "action",
                "action": "open",
                "target": "Google",
                "is_action": True,
            },
        ),
        (
            "CASE 4 — web",
            "tìm trên web giá iPhone",
            {
                "intent": "web",
                "tool": "web",
                "query": "giá iPhone",
            },
        ),
    ]

    for title, message, decision in cases:

        print()
        print(title)
        print("message  :", message)
        print("decision :", decision)

        try:
            result = router_guard.validate_route(
                message,
                decision,
            )

            print("valid    :", getattr(
                result,
                "valid",
                None,
            ))

            print("intent   :", getattr(
                result,
                "intent",
                None,
            ))

            print("tool     :", getattr(
                result,
                "tool",
                None,
            ))

            print("action   :", getattr(
                result,
                "action",
                None,
            ))

            print("target   :", getattr(
                result,
                "target",
                None,
            ))

            print("query    :", getattr(
                result,
                "query",
                None,
            ))

            print("reason   :", getattr(
                result,
                "reason",
                None,
            ))

        except Exception as exc:
            print("[FAIL] router case")
            print(f"       {exc}")
            traceback.print_exc()

    print()
    print("ROUTER SELF CHECK:")

    try:
        checks = router_guard._self_check()

        for name, ok in checks.items():
            print(
                f"[{'PASS' if ok else 'FAIL'}] "
                f"{name}"
            )

    except Exception as exc:
        print("[FAIL] router self_check")
        print(f"       {exc}")

    return True


# ============================================================
# BRAIN → ROUTER
# ============================================================

def test_brain_to_router():
    banner("03. BRAIN → ROUTER")

    try:
        import brain
        import router_guard

        importlib.reload(brain)
        importlib.reload(router_guard)

    except Exception as exc:
        print("[FAIL] import brain/router")
        print(f"       {exc}")
        return False

    messages = [
        "mấy giờ rồi",
        "hôm nay là ngày bao nhiêu",
        "mở Google",
        "tìm trên web giá iPhone",
        "xin chào",
    ]

    for message in messages:

        print()
        print("MESSAGE:", message)

        try:
            decision = brain.think(
                message
            )

            print()
            print("BRAIN")
            print(" intent =", getattr(
                decision,
                "intent",
                None,
            ))
            print(" action =", getattr(
                decision,
                "action",
                None,
            ))
            print(" tool   =", getattr(
                decision,
                "tool",
                None,
            ))
            print(" target =", getattr(
                decision,
                "target",
                None,
            ))
            print(" query  =", getattr(
                decision,
                "query",
                None,
            ))
            print(" is_action =", getattr(
                decision,
                "is_action",
                None,
            ))

            route = router_guard.validate_route(
                message,
                decision,
            )

            print()
            print("ROUTER")
            print(" valid  =", getattr(
                route,
                "valid",
                None,
            ))
            print(" intent =", getattr(
                route,
                "intent",
                None,
            ))
            print(" tool   =", getattr(
                route,
                "tool",
                None,
            ))
            print(" action =", getattr(
                route,
                "action",
                None,
            ))
            print(" target =", getattr(
                route,
                "target",
                None,
            ))
            print(" reason =", getattr(
                route,
                "reason",
                None,
            ))

        except Exception as exc:
            print("[FAIL]")
            print(f"       {exc}")
            traceback.print_exc()


# ============================================================
# WEB CONTEXT
# ============================================================

def test_web_context():
    banner("04. WEB CONTEXT — IMPORT + BASIC")

    try:
        import web_context

        importlib.reload(web_context)

        print("[PASS] import web_context")

        # Tìm constructor WebSource
        source = web_context.WebSource(
            number=2,
            title="Test source",
            url="https://example.com",
            snippet="Test snippet",
        )

        print("[PASS] WebSource")
        print(source)

        return True

    except Exception as exc:
        print("[FAIL] web_context")
        print(f"       {exc}")
        traceback.print_exc()
        return False


# ============================================================
# MAIN SELF CHECK
# ============================================================

def test_main():
    banner("05. MAIN SELF CHECK")

    try:
        import main

        importlib.reload(main)

        print("[PASS] import main")

        result = main.self_check()

        print()
        print("MAIN SELF CHECK RESULT:")
        print(result)

        return True

    except Exception as exc:
        print("[FAIL] main")
        print(f"       {exc}")
        traceback.print_exc()
        return False


# ============================================================
# FINAL
# ============================================================

def main():
    banner(
        "MINH MINI — FINAL REPAIR 02"
    )

    syntax_check(
        "response_guard.py"
    )

    syntax_check(
        "router_guard.py"
    )

    syntax_check(
        "web_context.py"
    )

    syntax_check(
        "main.py"
    )

    test_response_guard()
    test_router_guard()
    test_brain_to_router()
    test_web_context()
    test_main()

    banner(
        "REPAIR 02 DIAGNOSTIC HOÀN TẤT"
    )

    print(
        "Chưa thay thế response_guard.py "
        "hoặc router_guard.py."
    )

    print(
        "Output trên sẽ được dùng để sửa "
        "đúng logic FINAL, tránh sửa mù."
    )


if __name__ == "__main__":
    main()