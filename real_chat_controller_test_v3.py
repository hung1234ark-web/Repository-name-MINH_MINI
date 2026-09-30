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

            if len(signature.parameters) >= 1:
                return name, fn

        except Exception:
            continue

    return "", None


def worker(queue):
    try:
        print("[WORKER 1] Finding Brain...", flush=True)

        brain_name, brain_function = find_brain_function()

        if brain_function is None:
            queue.put({
                "ok": False,
                "stage": "brain",
                "error": "Không tìm thấy Brain function.",
            })
            return

        print(
            f"[WORKER 2] Brain = {brain_name}",
            flush=True,
        )

        print("[WORKER 3] Calling Brain...", flush=True)

        decision = brain_function(MESSAGE)

        print(
            f"[WORKER 4] Brain returned: "
            f"intent={getattr(decision, 'intent', '')}, "
            f"tool={getattr(decision, 'tool', '')}",
            flush=True,
        )

        print("[WORKER 5] Calling Router...", flush=True)

        route = router_guard.validate_route(
            MESSAGE,
            decision,
        )

        print(
            f"[WORKER 6] Router returned: "
            f"valid={getattr(route, 'valid', '')}, "
            f"tool={getattr(route, 'tool', '')}",
            flush=True,
        )

        print("[WORKER 7] Creating Controller...", flush=True)

        controller = ExecutionController(
            handlers={
                "chat": chat.handle_chat,
                "ollama": chat.handle_chat,
            }
        )

        print("[WORKER 8] Controller created.", flush=True)

        print(
            "[WORKER 9] Calling Controller.execute()...",
            flush=True,
        )

        started = time.time()

        result = controller.execute(
            message=MESSAGE,
            decision=decision,
        )

        elapsed = time.time() - started

        print(
            f"[WORKER 10] Controller returned "
            f"after {elapsed:.2f}s",
            flush=True,
        )

        queue.put({
            "ok": True,
            "brain_name": brain_name,
            "decision": decision,
            "route": route,
            "result": result,
            "controller_time": elapsed,
        })

    except Exception as exc:
        queue.put({
            "ok": False,
            "stage": "worker",
            "error": f"{type(exc).__name__}: {exc}",
        })


def main():
    print("=" * 70)
    print("MINH MINI - REAL CHAT CONTROLLER TEST V3")
    print("=" * 70)
    print(f"MESSAGE: {MESSAGE}")
    print()

    print("[1] CHAT HANDLER")
    print(
        "handle_chat:",
        chat.handle_chat,
    )
    print(
        "signature:",
        inspect.signature(chat.handle_chat),
    )
    print()

    print("[2] STARTING PIPELINE")
    print("    TIMEOUT: 45 seconds")
    print()

    queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=worker,
        args=(queue,),
    )

    started = time.time()

    process.start()

    process.join(45)

    elapsed = time.time() - started

    print()
    print(f"PROCESS EXIT CODE: {process.exitcode}")
    print(f"TIME: {elapsed:.2f}s")
    print()

    if process.is_alive():
        process.terminate()
        process.join()

        print("[FAIL] PIPELINE TIMEOUT")
        print()
        print(">>> REAL CHAT CONTROLLER V3: FAIL")
        return

    if queue.empty():
        print("[FAIL] NO RESULT FROM WORKER")
        print()
        print(">>> REAL CHAT CONTROLLER V3: FAIL")
        return

    data = queue.get()

    if not data.get("ok"):
        print("[FAIL] WORKER")
        print(f"STAGE: {data.get('stage', '')}")
        print(f"ERROR: {data.get('error', '')}")
        print()
        print(">>> REAL CHAT CONTROLLER V3: FAIL")
        return

    decision = data["decision"]
    route = data["route"]
    result = data["result"]

    print("[PASS] BRAIN")
    print(
        f"      intent={getattr(decision, 'intent', '')}"
    )
    print(
        f"      tool={getattr(decision, 'tool', '')}"
    )
    print()

    print("[PASS] ROUTER")
    print(
        f"      valid={getattr(route, 'valid', '')}"
    )
    print(
        f"      intent={getattr(route, 'intent', '')}"
    )
    print(
        f"      tool={getattr(route, 'tool', '')}"
    )
    print()

    print("[PASS] EXECUTION CONTROLLER")
    print(
        f"      success={getattr(result, 'success', '')}"
    )
    print(
        f"      metadata={getattr(result, 'metadata', {})}"
    )
    print(
        f"      controller_time={data['controller_time']:.2f}s"
    )
    print()

    response = str(
        getattr(result, "response", "") or ""
    ).strip()

    if not response:
        print("[FAIL] EMPTY CHAT RESPONSE")
        print()
        print(">>> REAL CHAT CONTROLLER V3: FAIL")
        return

    print("[PASS] REAL CHAT RESPONSE")
    print(f"      {response}")
    print()

    bad_response = (
        "Chưa có nguồn thông tin nào được cung cấp"
        in response
        or
        "Chưa có dữ liệu hoặc nguồn thông tin nào"
        in response
    )

    if bad_response:
        print("[FAIL] WRONG CHAT HANDLER")
        print("      Vẫn nhận Web AI response.")
        print()
        print(">>> REAL CHAT CONTROLLER V3: FAIL")
        return

    print("=" * 70)
    print("REAL CHAT CONTROLLER V3 COMPLETE")
    print("=" * 70)
    print(">>> REAL CHAT CONTROLLER V3: PASS")


if __name__ == "__main__":
    main()
