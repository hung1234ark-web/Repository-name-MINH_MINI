import time
import requests


URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:1.7b"

PAYLOAD = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Trả lời đúng một câu ngắn: MINH MINI đang hoạt động.",
        }
    ],
    "stream": False,
}


def main():
    print("=" * 70)
    print("MINH MINI - DIRECT OLLAMA API TEST")
    print("=" * 70)

    print("URL  :", URL)
    print("MODEL:", MODEL)
    print()

    start = time.perf_counter()

    try:
        print("[1/3] Connecting to Ollama...")

        response = requests.post(
            URL,
            json=PAYLOAD,
            timeout=(5, 30),
        )

        elapsed = time.perf_counter() - start

        print("[2/3] HTTP response received")
        print("       STATUS:", response.status_code)
        print(f"       TIME  : {elapsed:.2f}s")

        response.raise_for_status()

        data = response.json()

        print("[3/3] JSON parsed")
        print("       TYPE:", type(data).__name__)

        message = data.get("message", {})
        answer = message.get("content", "")

        print()
        print("MODEL RESPONSE:")
        print(repr(answer))

        if answer.strip():
            print()
            print("[PASS] DIRECT OLLAMA API")
        else:
            print()
            print("[FAIL] Ollama returned empty content")

    except requests.exceptions.Timeout as exc:
        elapsed = time.perf_counter() - start
        print()
        print("[FAIL] OLLAMA TIMEOUT")
        print(f"       TIME: {elapsed:.2f}s")
        print("       ERROR:", exc)

    except requests.exceptions.ConnectionError as exc:
        elapsed = time.perf_counter() - start
        print()
        print("[FAIL] OLLAMA CONNECTION")
        print(f"       TIME: {elapsed:.2f}s")
        print("       ERROR:", exc)

    except requests.exceptions.HTTPError as exc:
        print()
        print("[FAIL] OLLAMA HTTP ERROR")
        print("       STATUS:", response.status_code)
        print("       ERROR:", exc)
        print("       BODY:", response.text[:2000])

    except Exception as exc:
        elapsed = time.perf_counter() - start
        print()
        print("[FAIL] UNEXPECTED ERROR")
        print(f"       TIME: {elapsed:.2f}s")
        print("       TYPE: {type(exc).__name__}")
        print("       ERROR:", exc)

    print()
    print("=" * 70)
    print("DIRECT OLLAMA API TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()