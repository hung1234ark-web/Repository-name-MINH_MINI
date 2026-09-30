import inspect
import multiprocessing as mp
import time

import brain
import router_guard
import execution_controller
import web_ai


MESSAGE = "Xin chào Minh, Lam đang kiểm tra chat thật."


def find_brain_api():
    candidates = []

    for name, value in inspect.getmembers(brain):
        if name.startswith("_"):
            continue

        if inspect.isfunction(value) or inspect.ismethod(value):
            candidates.append((name, value))

    preferred = (
        "think",
        "process",
        "analyze",
        "understand",
        "decide",
    )

    for preferred_name in preferred:
        for name, function in candidates:
            if name == preferred_name:
                return name, function

    for name, function in candidates:
        try:
            signature = inspect.signature(function)
            parameters = list(signature.parameters.values())

            if len(parameters) >= 1:
                return name, function
        except Exception:
            continue

    return None, None


def run_controller(message, queue):
    try:
        brain_name, brain_function = find_brain_api()

        if brain_function is None:
            raise RuntimeError(
                "Không tìm thấy Brain API callable trong brain.py"
            )

        decision = brain_function(message)

        route = router_guard.validate_route(
            message,
            decision,
        )

        handler = web_ai.call_ollama

        controller = execution_controller.ExecutionController(
            handlers={
                "chat": handler,
                "ollama": handler,
            }
        )

        result = controller.execute(
            message=message,
            decision=decision,
        )

        queue.put(
            {
                "ok": True,
                "brain_name": brain_name,
                "decision": repr(decision),
                "route": repr(route),
                "result": repr(result),
            }
        )

    except Exception as exc:
        queue.put(
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )


def main():
    print("=" * 70)
    print("MINH MINI - REAL CHAT CONTROLLER TEST")
    print("=" * 70)

    print("MESSAGE:", MESSAGE)
    print()

    print("[1] Inspecting Brain API...")

    brain_name, brain_function = find_brain_api()

    if brain_function is None:
        print("[FAIL] Không tìm thấy Brain API.")
        print()
        print("Các callable trong brain.py:")

        for name, value in inspect.getmembers(brain):
            if name.startswith("_"):
                continue

            if inspect.isfunction(value) or inspect.ismethod(value):
                try:
                    print(
                        f"       {name}{inspect.signature(value)}"
                    )
                except Exception:
                    print(f"       {name}")

        return

    print("[PASS] Brain API")
    print("      NAME:", brain_name)
    print("      SIGNATURE:", inspect.signature(brain_function))

    print()
    print("[2] Checking Ollama handler...")

    handler = getattr(
        web_ai,
        "call_ollama",
        None,
    )

    if not callable(handler):
        print("[FAIL] call_ollama không callable.")
        return

    print("[PASS] call_ollama")
    print("      signature:", inspect.signature(handler))

    print()
    print("[3] Running Brain -> Router -> Controller...")
    print("    TIMEOUT: 90 seconds")
    print()

    queue = mp.Queue()

    process = mp.Process(
        target=run_controller,
        args=(MESSAGE, queue),
    )

    start = time.perf_counter()

    process.start()
    process.join(90)

    elapsed = time.perf_counter() - start

    if process.is_alive():
        print("[FAIL] controller timeout")
        print(f"      TIME: {elapsed:.2f}s")

        process.terminate()
        process.join(5)

        print("      Test process đã được dừng.")
        return

    print("PROCESS EXIT CODE:", process.exitcode)
    print(f"TIME: {elapsed:.2f}s")

    if queue.empty():
        print("[FAIL] Không nhận được kết quả từ controller.")
        return

    data = queue.get()

    if not data.get("ok"):
        print("[FAIL] REAL CHAT CONTROLLER")
        print("      TYPE:", data.get("error_type"))
        print("      ERROR:", data.get("error"))
        return

    print()
    print("[PASS] BRAIN DECISION")
    print(data["decision"])

    print()
    print("[PASS] ROUTER")
    print(data["route"])

    print()
    print("[PASS] EXECUTION CONTROLLER")
    print(data["result"])

    print()
    print("=" * 70)
    print("REAL CHAT CONTROLLER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()