import inspect
import brain


def show_function(name):
    obj = getattr(brain, name, None)

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    if obj is None:
        print("KHONG TON TAI")
        return

    print("OBJECT :", obj)
    print("SIGNATURE:", end=" ")

    try:
        print(inspect.signature(obj))
    except Exception as exc:
        print(f"<khong lay duoc: {exc}>")

    try:
        print("\nSOURCE:")
        print(inspect.getsource(obj))
    except Exception as exc:
        print(f"<khong lay duoc source: {exc}>")


print("=" * 70)
print("MINH MINI — BRAIN ROUTING INSPECT")
print("=" * 70)

for name in [
    "think",
    "normalize_text",
    "classify_intent",
    "detect_intent",
    "detect_action",
    "detect_tool",
    "extract_topic",
    "extract_target",
    "build_decision",
]:
    show_function(name)

print("\n" + "=" * 70)
print("MODULE GLOBALS LIEN QUAN")
print("=" * 70)

for name in sorted(dir(brain)):
    low = name.lower()

    if any(
        key in low
        for key in (
            "web",
            "search",
            "time",
            "date",
            "memory",
            "target",
            "intent",
            "action",
            "context",
            "route",
        )
    ):
        print(name)

print("\n>>> INSPECT BRAIN ROUTING DONE")










