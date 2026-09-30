import inspect
import multiprocessing
import time

import brain
import router_guard
import chat
from execution_controller import ExecutionController


MESSAGE = "Xin chào Minh, Lam đang kiểm tra chat thật."


def find_brain_function():
    preferred = [
        "think",
        "process",
        "analyze",
        "understand",
        "decide",
    ]

    for name in preferred:
        fn = getattr(brain, name, None)
        if callable(fn):
            return name, fn

    for name, fn in inspect.getmembers(brain, inspect.isfunction):
        if name.startswith("_"):
            continue

        try:
            signature = inspect.signature(fn)
            parameters = list(signature.parameters.values())

            if parameters:
                return name, fn
        except Exception:
            continue

    return "", None


def worker(queue):
    try:
        brain_name, brain_function = find_brain_function()

        if brain_function is None:
            queue.put({
                "ok": False,
                "stage": "brain",
                "error": "Không tìm thấy Brain function.",
            })
            return

        decision = brain_function(MESSAGE)

        route = router_guard.validate_route(
            MESSAGE,
            decision,
        )

        handlers = {
            "chat": chat.handle_chat,
            "ollama": chat.handle_chat,
        }

        controller = ExecutionController(
            handlers=handlers,
        )

        result = controller.execute(
            message=MESSAGE,
            decision=decision,
        )

        queue.put({
            "ok": True,
            "brain_name": brain_name,
            "decision": decision,
            "route": route,
            "result": result,
        })

    except Exception as exc:
        queue.put({
            "ok": False,
            "stage": "pipeline",
            "error": f"{type(exc).__name__}: {exc}",
        })


def main():
    print("=" * 70)
    print("MINH MINI - REAL CHAT CONTROLLER TEST V2")
    print("=" * 70)
    print(f"MESSAGE: {MESSAGE}")
    print()

    print("[1] Checking Chat Handler...")
    print(f"      handle_chat: {chat.handle_chat}")
    print(
        f"      signature: "
        f"{inspect.signature(chat.handle_chat)}"
    )
    print()

    print("[2] Running Brain -> Router -> Controller -> Chat -> Ollama...")
    print("    TIMEOUT: 90 seconds")
    print()

    queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=worker,
        args=(queue,),
    )

    started = time.time()
    process.start()

    process.join(90)

    elapsed = time.time() - started

    if process.is_alive():
        process.terminate()
        process.join()

        print("[FAIL] PIPELINE TIMEOUT")
        print(f"      TIME: {elapsed:.2f}s")
        print()
        print(">>> REAL CHAT CONTROLLER V2: FAIL")
        return

    print(f"PROCESS EXIT CODE: {process.exitcode}")
    print(f"TIME: {elapsed:.2f}s")
    print()

    if queue.empty():
        print("[FAIL] NO RESULT")
        print()
        print(">>> REAL CHAT CONTROLLER V2: FAIL")
        return

    data = queue.get()

    if not data.get("ok"):
        print("[FAIL] PIPELINE")
        print(f"      STAGE: {data.get('stage', '')}")
        print(f"      ERROR: {data.get('error', '')}")
        print()
        print(">>> REAL CHAT CONTROLLER V2: FAIL")
        return

    decision = data["decision"]
    route = data["route"]
    result = data["result"]

    print("[PASS] BRAIN")
    print(f"      FUNCTION: {data['brain_name']}")
    print(f"      INTENT: {getattr(decision, 'intent', '')}")
    print(f"      TOOL: {getattr(decision, 'tool', '')}")
    print()

    print("[PASS] ROUTER")
    print(f"      VALID: {getattr(route, 'valid', '')}")
    print(f"      INTENT: {getattr(route, 'intent', '')}")
    print(f"      TOOL: {getattr(route, 'tool', '')}")
    print()

    print("[PASS] EXECUTION CONTROLLER")
    print(f"      SUCCESS: {getattr(result, 'success', '')}")
    print(f"      HANDLER: {getattr(result, 'metadata', {})}")
    print()

    response = str(
        getattr(result, "response", "") or ""
    ).strip()

    if response:
        print("[PASS] REAL CHAT RESPONSE")
        print(f"      {response}")
    else:
        print("[FAIL] REAL CHAT RESPONSE")
        print("      Controller trả response rỗng.")
        print()
        print(">>> REAL CHAT CONTROLLER V2: FAIL")
        return

    bad_web_ai_response = (
        "Chưa có nguồn thông tin nào được cung cấp"
        in response
        or
        "Chưa có dữ liệu hoặc nguồn thông tin nào"
        in response
    )

    if bad_web_ai_response:
        print()
        print("[FAIL] CHAT ROLE")
        print("      Controller vẫn đang dùng Web AI response.")
        print()
        print(">>> REAL CHAT CONTROLLER V2: FAIL")
        return

    print()
    print("=" * 70)
    print("REAL CHAT CONTROLLER V2 COMPLETE")
    print("=" * 70)
    print(">>> REAL CHAT CONTROLLER V2: PASS")


if __name__ == "__main__":
    main()