# ============================================================
# MINH MINI — INTEGRATION TEST FINAL
# Brain → Router → Controller → Response Guard
# ============================================================

from __future__ import annotations

import inspect


# ============================================================
# TEST ENGINE
# ============================================================

TOTAL = 0
PASS = 0
FAIL = 0
FAILURES = []


def test(name, fn):
    global TOTAL, PASS, FAIL

    TOTAL += 1

    try:
        result = fn()

        if result is False:
            raise AssertionError("Test trả về False")

        PASS += 1

        print(f"[PASS] {name}")

        if result not in (None, True):
            print(f"       {result}")

    except Exception as e:
        FAIL += 1
        FAILURES.append((name, repr(e)))

        print(f"[FAIL] {name}")
        print(f"       {e!r}")


# ============================================================
# IMPORT
# ============================================================

print("=" * 60)
print("MINH MINI — INTEGRATION TEST FINAL")
print("=" * 60)

import brain
import router_guard
import execution_controller
import response_guard
import main
import conversation_state

print("[IMPORT] core modules: OK")


# ============================================================
# GENERIC
# ============================================================

def result_text(value):
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
            "content",
            "result",
        ):
            if key in value and value[key] is not None:
                return str(value[key]).strip()

    for attr in (
        "response",
        "answer",
        "text",
        "message",
        "content",
        "result",
    ):
        if hasattr(value, attr):
            item = getattr(value, attr)

            if item is not None:
                return str(item).strip()

    return str(value).strip()


# ============================================================
# 01. BRAIN
# ============================================================

print()
print("=" * 60)
print("01. BRAIN")
print("=" * 60)


brain_obj = brain.BrainCore()

brain_results = {}


def brain_test(message):

    def run():
        result = brain_obj.think(message)

        if result is None:
            raise RuntimeError(
                "Brain.think() trả về None"
            )

        brain_results[message] = result

        return result

    return run


test(
    "brain:mấy giờ rồi",
    brain_test("mấy giờ rồi"),
)

test(
    "brain:hôm nay là ngày bao nhiêu",
    brain_test("hôm nay là ngày bao nhiêu"),
)

test(
    "brain:mở Google",
    brain_test("mở Google"),
)

test(
    "brain:tìm trên web giá iPhone",
    brain_test("tìm trên web giá iPhone"),
)

test(
    "brain:xin chào",
    brain_test("xin chào"),
)


# ============================================================
# 02. BRAIN → ROUTER
# ============================================================

print()
print("=" * 60)
print("02. BRAIN → ROUTER")
print("=" * 60)


def router_test(message):

    def run():
        decision = brain_results.get(message)

        if decision is None:
            raise RuntimeError(
                f"Không có BrainDecision: {message}"
            )

        # API THẬT của router_guard.py
        routed = router_guard.validate_route(
            message,
            decision,
        )

        if routed is None:
            raise RuntimeError(
                "validate_route() trả về None"
            )

        if not getattr(routed, "valid", False):
            raise RuntimeError(
                f"Router reject: {routed!r}"
            )

        return routed

    return run


test(
    "brain_router:mấy giờ rồi",
    router_test("mấy giờ rồi"),
)

test(
    "brain_router:hôm nay là ngày bao nhiêu",
    router_test("hôm nay là ngày bao nhiêu"),
)

test(
    "brain_router:mở Google",
    router_test("mở Google"),
)

test(
    "brain_router:tìm trên web giá iPhone",
    router_test("tìm trên web giá iPhone"),
)

test(
    "brain_router:xin chào",
    router_test("xin chào"),
)


# ============================================================
# 03. EXECUTION CONTROLLER
# ============================================================

print()
print("=" * 60)
print("03. EXECUTION CONTROLLER")
print("=" * 60)


# Controller thật chỉ nhận:
#
# ExecutionController(handlers=None)
#
# execute(message='', decision=None)

Controller = execution_controller.ExecutionController


def fake_action(message="", **kwargs):
    return f"[FAKE ACTION] {message}"


def fake_web(message="", **kwargs):
    return "[FAKE WEB] Đã tìm kiếm."


def fake_chat(message="", **kwargs):
    return "[FAKE CHAT] Xin chào Lam!"


# Handler map theo kiến trúc thật.
handlers = {
    "action": fake_action,
    "web": fake_web,
    "chat": fake_chat,
    "ollama": fake_chat,
}


controller = Controller(
    handlers=handlers
)


controller_results = {}


def controller_test(message):

    def run():

        # Brain tạo decision.
        decision = brain_results.get(message)

        if decision is None:
            raise RuntimeError(
                f"Không có BrainDecision: {message}"
            )

        # Controller nhận decision,
        # KHÔNG nhận intent/tool riêng lẻ.
        result = controller.execute(
            message=message,
            decision=decision,
        )

        if result is None:
            raise RuntimeError(
                "Controller.execute() trả về None"
            )

        controller_results[message] = result

        response = getattr(
            result,
            "response",
            None,
        )

        if not response:
            response = result_text(result)

        if not response:
            raise RuntimeError(
                f"Controller response rỗng: {result!r}"
            )

        return result

    return run


test(
    "controller:mở Google",
    controller_test("mở Google"),
)

test(
    "controller:tìm trên web giá iPhone",
    controller_test(
        "tìm trên web giá iPhone"
    ),
)

test(
    "controller:xin chào",
    controller_test("xin chào"),
)


# ============================================================
# 04. EXECUTION → RESPONSE GUARD
# ============================================================

print()
print("=" * 60)
print("04. EXECUTION → RESPONSE GUARD")
print("=" * 60)


def response_guard_test():

    result = controller_results.get(
        "xin chào"
    )

    if result is None:
        raise RuntimeError(
            "Không có kết quả chat từ Controller."
        )

    response = getattr(
        result,
        "response",
        None,
    )

    if not response:
        response = result_text(result)

    if not response:
        raise RuntimeError(
            f"Response rỗng: {result!r}"
        )

    decision = brain_results.get(
        "xin chào"
    )

    guard = response_guard.validate_response(
        "xin chào",
        response,
        decision=decision,
        execution_result=result,
    )

    if not getattr(
        guard,
        "valid",
        False,
    ):
        raise RuntimeError(
            f"Response Guard reject: {guard!r}"
        )

    return (
        f"valid=True, "
        f"answer={getattr(guard, 'answer', response)!r}"
    )


test(
    "response_guard_success",
    response_guard_test,
)


# ============================================================
# 05. ACTION SAFETY
# ============================================================

print()
print("=" * 60)
print("05. ACTION SAFETY")
print("=" * 60)


def get_action_result():

    result = controller_results.get(
        "mở Google"
    )

    if result is None:
        raise RuntimeError(
            "Không có action result."
        )

    return result


def action_target_test():

    result = get_action_result()

    decision = brain_results.get(
        "mở Google"
    )

    if decision is None:
        raise RuntimeError(
            "Không có BrainDecision action."
        )

    if getattr(
        decision,
        "intent",
        None,
    ) != "action":
        raise RuntimeError(
            f"Brain intent sai: {decision!r}"
        )

    target = getattr(
        decision,
        "target",
        None,
    )

    if target != "google":
        raise RuntimeError(
            f"Action target sai: {target!r}"
        )

    return f"target={target}"


def action_tool_test():

    result = get_action_result()

    decision = brain_results.get(
        "mở Google"
    )

    tool = getattr(
        decision,
        "tool",
        None,
    )

    if tool != "action":
        raise RuntimeError(
            f"Action tool sai: {tool!r}"
        )

    return f"tool={tool}"


test(
    "action_target",
    action_target_test,
)

test(
    "action_tool",
    action_tool_test,
)


# ============================================================
# 06. EMPTY INPUT
# ============================================================

print()
print("=" * 60)
print("06. EMPTY INPUT")
print("=" * 60)


def empty_brain_test():

    result = brain_obj.think("")

    if result is None:
        raise RuntimeError(
            "Brain.think('') trả về None"
        )

    # Empty input phải an toàn,
    # không được exception.
    return (
        "Brain.think('') an toàn → "
        f"{result!r}"
    )


test(
    "empty_brain_safe",
    empty_brain_test,
)


def empty_router_test():

    result = router_guard.validate_route(
        "",
        brain_obj.think(""),
    )

    if result is None:
        raise RuntimeError(
            "Router trả về None với empty input"
        )

    return (
        f"valid={getattr(result, 'valid', None)}"
    )


test(
    "empty_router_safe",
    empty_router_test,
)


# ============================================================
# 07. TYPO TOLERANCE
# ============================================================

print()
print("=" * 60)
print("07. TYPO TOLERANCE")
print("=" * 60)


test(
    "typo:mấy h rồi",
    lambda: (
        f"normalize_text="
        f"{brain.normalize_text('mấy h rồi')!r}"
    ),
)

test(
    "typo:iphonee",
    lambda: (
        f"normalize_text="
        f"{brain.normalize_text('iphonee')!r}"
    ),
)


# ============================================================
# 08. CONVERSATION CONTEXT
# ============================================================

print()
print("=" * 60)
print("08. CONVERSATION CONTEXT")
print("=" * 60)


test(
    "context_build",
    lambda: (
        f"module available: "
        f"{[x for x in dir(conversation_state) if not x.startswith('_')]}"
    ),
)


def context_topic_test():

    topic = conversation_state.extract_topic(
        "giá iPhone"
    )

    if not topic:
        raise RuntimeError(
            "Không lấy được topic"
        )

    return f"topic={topic}"


test(
    "context_topic",
    context_topic_test,
)


# ============================================================
# 09. PUBLIC API
# ============================================================

print()
print("=" * 60)
print("09. PUBLIC API")
print("=" * 60)


def public_api(name):

    def run():

        fn = getattr(
            main,
            name,
            None,
        )

        if not callable(fn):
            raise RuntimeError(
                f"main.{name} không tồn tại"
            )

        return f"callable={name}"

    return run


test(
    "main.process",
    public_api("process"),
)

test(
    "main.ask",
    public_api("ask"),
)

test(
    "main.chat",
    public_api("chat"),
)

test(
    "main.status",
    public_api("status"),
)

test(
    "main.self_check",
    public_api("self_check"),
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)
print("MINH MINI — INTEGRATION TEST RESULT")
print("=" * 60)

print(f"TOTAL : {TOTAL}")
print(f"PASS  : {PASS}")
print(f"FAIL  : {FAIL}")


if FAIL:

    print()
    print("Các mục FAIL:")

    for name, error in FAILURES:
        print(f" - {name}")
        print(f"   {error}")

    print()
    print(
        ">>> INTEGRATION TEST: CÒN LỖI CẦN SỬA"
    )

else:

    print()
    print(
        ">>> INTEGRATION TEST: PASS"
    )

    print(
        ">>> BRAIN → ROUTER → CONTROLLER → RESPONSE GUARD: PASS"
    )


if __name__ == "__main__":
    raise SystemExit(
        1 if FAIL else 0
    )