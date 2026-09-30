import inspect
import main


print("=" * 70)
print("MINH MINI - MAIN STRUCTURE INSPECTION")
print("=" * 70)

print()
print("MODULE:", main.__file__)

print()
print("=== FUNCTIONS ===")

for name, obj in inspect.getmembers(main, inspect.isfunction):
    try:
        signature = inspect.signature(obj)
    except Exception:
        signature = "(signature unavailable)"

    print(f"{name}{signature}")

print()
print("=== IMPORTANT GLOBALS ===")

names = [
    "MINH",
    "brain",
    "router_guard",
    "response_guard",
    "execution_controller",
    "action",
    "web",
    "web_ai",
    "web_context",
    "chat_module",
    "ollama_chat",
    "create_controller",
    "create_brain",
    "handle_action",
    "handle_web",
]

for name in names:
    exists = hasattr(main, name)

    if exists:
        value = getattr(main, name)

        try:
            value_type = type(value).__name__
        except Exception:
            value_type = "unknown"

        print(f"[FOUND] {name} -> {value_type}")
    else:
        print(f"[----]  {name}")

print()
print("=== MAIN CLASS ===")

for name, obj in inspect.getmembers(main, inspect.isclass):
    if obj.__module__ == main.__name__:
        print(f"CLASS: {name}")

        for method_name, method in inspect.getmembers(
            obj,
            inspect.isfunction,
        ):
            try:
                signature = inspect.signature(method)
            except Exception:
                signature = "(signature unavailable)"

            print(f"    {method_name}{signature}")

print()
print("=" * 70)
print(">>> INSPECTION COMPLETE")
print("=" * 70)