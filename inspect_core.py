import inspect
import main


print("=" * 70)
print("MINH MINI - CORE STRUCTURE INSPECTION FINAL")
print("=" * 70)

print()
print("SOURCE:", main.__file__)

targets = [
    "create_brain",
    "create_controller",
    "process",
    "status",
    "ask",
    "chat",
    "self_check",
    "main",
]

for name in targets:

    print()
    print("=" * 70)
    print(f"=== {name}() ===")
    print("=" * 70)

    obj = getattr(main, name, None)

    if obj is None:
        print("[MISSING]")
        continue

    try:
        print(inspect.getsource(obj))
    except Exception as exc:
        print(
            "[ERROR]",
            type(exc).__name__,
            exc,
        )


print()
print("=" * 70)
print("=== GLOBAL CORE OBJECTS ===")
print("=" * 70)

for name in [
    "MINH",
    "MinhMiniCore",
    "brain_module",
    "router_guard",
    "response_guard",
    "execution_controller",
    "chat_module",
    "controller",
]:

    value = getattr(main, name, None)

    if value is None:
        print(f"[MISSING] {name}")
    else:
        print(
            f"[FOUND] {name} -> "
            f"{type(value).__name__}"
        )


print()
print("=" * 70)
print("=== CLASS DEFINITIONS IN MAIN ===")
print("=" * 70)

classes = inspect.getmembers(
    main,
    inspect.isclass,
)

for name, obj in classes:

    if getattr(obj, "__module__", None) == main.__name__:

        print()
        print(
            f"[CLASS] {name}"
        )

        try:
            print(
                inspect.getsource(obj)
            )
        except Exception as exc:
            print(
                "[ERROR]",
                type(exc).__name__,
                exc,
            )


print()
print("=" * 70)
print(">>> CORE STRUCTURE INSPECTION COMPLETE")
print("=" * 70)