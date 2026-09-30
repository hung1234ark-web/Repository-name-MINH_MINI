import inspect
import brain


NAMES = [
    "think",
    "detect_intent",
    "extract_action",
    "extract_target",
    "merge_context",
    "scan_history_context",
    "get_context_from_module",
]


print("=" * 70)
print("MINH MINI — BRAIN CORE INSPECT")
print("=" * 70)

for name in NAMES:
    obj = getattr(brain, name, None)

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    if obj is None:
        print("KHONG TON TAI")
        continue

    print("OBJECT:", obj)

    try:
        print("SIGNATURE:", inspect.signature(obj))
    except Exception as exc:
        print("SIGNATURE ERROR:", exc)

    try:
        print("\nSOURCE:")
        print(inspect.getsource(obj))
    except Exception as exc:
        print("SOURCE ERROR:", exc)


print("\n" + "=" * 70)
print("CONSTANTS")
print("=" * 70)

for name in [
    "ACTION_PATTERNS",
    "TARGET_ALIASES",
    "TOPIC_HINTS",
]:
    obj = getattr(brain, name, None)

    print(f"\n{name}:")
    print(repr(obj))


print("\n>>> BRAIN CORE INSPECT DONE")