import inspect
import chat


print("=" * 80)
print("MINH MINI — CHAT OLLAMA LANGUAGE SOURCE")
print("=" * 80)

fn = getattr(chat, "call_chat_ollama", None)

print()
print("call_chat_ollama:", fn)

if fn is None:
    print("[FAIL] Không tìm thấy call_chat_ollama")
else:
    print()
    print("SIGNATURE:")
    print(inspect.signature(fn))

    print()
    print("SOURCE:")
    print(inspect.getsource(fn))

print()
print("=" * 80)
print("CHAT MODULE FUNCTIONS")
print("=" * 80)

for name, obj in inspect.getmembers(chat, inspect.isfunction):
    if (
        "ollama" in name.lower()
        or "chat" in name.lower()
        or "prompt" in name.lower()
        or "response" in name.lower()
    ):
        print()
        print("-" * 80)
        print(name)
        print(inspect.signature(obj))
        print(inspect.getsource(obj))

print()
print("=" * 80)
print("DONE")
print("=" * 80)
