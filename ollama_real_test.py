

from __future__ import annotations

import time
import inspect


print("=" * 70)
print("MINH MINI — REAL OLLAMA TEST")
print("=" * 70)


# ============================================================
# IMPORT
# ============================================================

try:
    import web_ai

    print("[PASS] import:web_ai")
except Exception as exc:
    print("[FAIL] import:web_ai")
    print(f"       {type(exc).__name__}: {exc}")
    raise SystemExit(1)


# ============================================================
# FIND HANDLER
# ============================================================

handler = getattr(web_ai, "call_ollama", None)

if not callable(handler):
    print("[FAIL] handler:call_ollama")
    print("       Không tìm thấy call_ollama trong web_ai.py")
    raise SystemExit(1)

print("[PASS] handler:call_ollama")
print(f"       {handler}")


# ============================================================
# SIGNATURE
# ============================================================

try:
    signature = inspect.signature(handler)

    print("[PASS] signature")
    print(f"       {signature}")

except Exception as exc:
    print("[FAIL] signature")
    print(f"       {type(exc).__name__}: {exc}")
    raise SystemExit(1)


# ============================================================
# REAL OLLAMA CALL
# ============================================================

prompt = (
    "Xin chào Minh. "
    "Hãy trả lời thật ngắn bằng tiếng Việt: "
    "MINH MINI đang hoạt động."
)

print()
print("--- REAL OLLAMA CALL ---")
print(f"PROMPT: {prompt}")

start = time.perf_counter()

try:
    result = handler(prompt)

    elapsed = time.perf_counter() - start

    print("[PASS] call_ollama")
    print(f"       TIME: {elapsed:.2f}s")
    print(f"       TYPE: {type(result).__name__}")
    print(f"       RESULT: {result!r}")

    if result is None:
        print("[WARN] Ollama trả về None.")

    elif isinstance(result, str) and not result.strip():
        print("[WARN] Ollama trả về chuỗi rỗng.")

    else:
        print("[PASS] non_empty_result")

except Exception as exc:

    elapsed = time.perf_counter() - start

    print("[FAIL] call_ollama")
    print(f"       TIME: {elapsed:.2f}s")
    print(f"       ERROR: {type(exc).__name__}: {exc}")


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("OLLAMA REAL TEST COMPLETE")
print("=" * 70)
