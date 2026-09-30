import inspect
import chat


print("=" * 80)
print("MINH MINI — CALL CHAT OLLAMA")
print("=" * 80)

fn = getattr(chat, "call_chat_ollama", None)

print()
print("FUNCTION:", fn)

if fn is None:
    print("[FAIL] Không tồn tại call_chat_ollama")
else:
    print()
    print("MODULE:", inspect.getmodule(fn))
    print("FILE:", inspect.getsourcefile(fn))
    print("SIGNATURE:", inspect.signature(fn))

    print()
    print("SOURCE:")
    print("-" * 80)
    print(inspect.getsource(fn))
    print("-" * 80)

print()
print("=" * 80)
print("CHAT GLOBALS LIÊN QUAN")
print("=" * 80)

for name, value in vars(chat).items():
    name_lower = name.lower()

    if any(
        key in name_lower
        for key in (
            "prompt",
            "system",
            "ollama",
            "model",
            "language",
            "url",
        )
    ):
        if callable(value):
            try:
                print()
                print(name)
                print(inspect.signature(value))
            except Exception:
                print(name, "-> callable")
        else:
            print(name, "=", repr(value))

print()
print("=" * 80)
print("DONE")
print("=" * 80)
