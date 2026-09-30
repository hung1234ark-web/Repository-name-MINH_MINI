import inspect
import multiprocessing as mp
import time
import traceback

import web_ai


PROMPT = "Trả lời thật ngắn bằng tiếng Việt: MINH MINI đang hoạt động."


def run_ollama(prompt, queue):
    try:
        result = web_ai.call_ollama(prompt)
        queue.put(
            {
                "ok": True,
                "type": type(result).__name__,
                "result": repr(result),
            }
        )
    except Exception as exc:
        queue.put(
            {
                "ok": False,
                "type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )


def main():
    print("=" * 70)
    print("MINH MINI - OLLAMA DEEP DIAGNOSTIC")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Handler
    # --------------------------------------------------------

    handler = getattr(web_ai, "call_ollama", None)

    if not callable(handler):
        print("[FAIL] call_ollama")
        print("       Không tìm thấy handler.")
        return

    print("[PASS] call_ollama")
    print("       signature:", inspect.signature(handler))

    # --------------------------------------------------------
    # 2. Config
    # --------------------------------------------------------

    print()
    print("--- CONFIG ---")

    get_config = getattr(web_ai, "get_ollama_config", None)

    if callable(get_config):
        try:
            config = get_config()

            print("[PASS] get_ollama_config")
            print("       TYPE:", type(config).__name__)
            print("       CONFIG:", repr(config))

        except Exception as exc:
            print("[FAIL] get_ollama_config")
            print(f"       {type(exc).__name__}: {exc}")
    else:
        print("[WARN] Không có get_ollama_config")

    # --------------------------------------------------------
    # 3. Source
    # --------------------------------------------------------

    print()
    print("--- CALL_OLLAMA SOURCE ---")

    try:
        source_file = inspect.getsourcefile(handler)
        source_lines, start_line = inspect.getsourcelines(handler)

        print("[PASS] source")
        print("       FILE:", source_file)
        print("       LINE:", start_line)

        print()
        print("       SOURCE:")

        for number, line in enumerate(
            source_lines[:50],
            start=start_line,
        ):
            print(f"       {number:04d}: {line.rstrip()}")

    except Exception as exc:
        print("[FAIL] source inspection")
        print(f"       {type(exc).__name__}: {exc}")

    # --------------------------------------------------------
    # 4. Real Ollama call
    # --------------------------------------------------------

    print()
    print("--- REAL OLLAMA CALL ---")
    print("PROMPT:", PROMPT)
    print("TIMEOUT: 90 seconds")
    print()

    queue = mp.Queue()

    process = mp.Process(
        target=run_ollama,
        args=(PROMPT, queue),
    )

    start = time.perf_counter()
    process.start()

    process.join(90)

    elapsed = time.perf_counter() - start

    # --------------------------------------------------------
    # 5. Timeout
    # --------------------------------------------------------

    if process.is_alive():

        print("[FAIL] Ollama timeout")
        print(f"       TIME: {elapsed:.2f}s")
        print("       call_ollama chưa trả kết quả sau 90 giây.")

        process.terminate()
        process.join(5)

        print("       Process Ollama test đã được dừng.")

    # --------------------------------------------------------
    # 6. Result
    # --------------------------------------------------------

    else:

        print(f"       PROCESS EXIT CODE: {process.exitcode}")

        if not queue.empty():

            data = queue.get()

            if data.get("ok"):

                print("[PASS] call_ollama returned")
                print(f"       TIME: {elapsed:.2f}s")
                print(f"       TYPE: {data['type']}")
                print(f"       RESULT: {data['result']}")

            else:

                print("[FAIL] call_ollama exception")
                print(f"       TIME: {elapsed:.2f}s")
                print(f"       ERROR: {data['type']}: {data['error']}")

                print()
                print("--- TRACEBACK ---")
                print(data["traceback"])

        else:

            print("[FAIL] Ollama process exited without result")
            print(f"       TIME: {elapsed:.2f}s")

    # --------------------------------------------------------
    # 7. End
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("OLLAMA DEEP DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()