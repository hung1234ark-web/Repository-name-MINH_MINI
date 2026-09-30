import time
import web_ai


def main():
    print("=" * 70)
    print("MINH MINI - CALL_OLLAMA FINAL HANDLER TEST")
    print("=" * 70)

    prompt = (
        "Hãy trả lời bằng tiếng Việt, tối đa 2 câu. "
        "Tên người dùng là Lam. "
        "Hãy nói rằng Minh Mini đã kết nối được với Ollama."
    )

    print("MODEL CONFIG:", web_ai.get_ollama_config())
    print("PROMPT:", prompt)
    print()

    start = time.perf_counter()

    try:
        result = web_ai.call_ollama(prompt)

        elapsed = time.perf_counter() - start

        print("[PASS] call_ollama returned")
        print(f"TIME: {elapsed:.2f}s")
        print(f"TYPE: {type(result).__name__}")
        print(f"RESULT: {result!r}")

        if isinstance(result, str) and result.strip():
            print()
            print("[PASS] NON_EMPTY_RESPONSE")
        else:
            print()
            print("[FAIL] EMPTY_RESPONSE")

    except Exception as exc:
        elapsed = time.perf_counter() - start

        print("[FAIL] call_ollama exception")
        print(f"TIME: {elapsed:.2f}s")
        print(f"TYPE: {type(exc).__name__}")
        print(f"ERROR: {exc}")

    print()
    print("=" * 70)
    print("FINAL HANDLER TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
