import inspect
import main


TARGETS = [
    ("main.ollama_chat", getattr(main, "ollama_chat", None)),
    ("main.chat", getattr(main, "chat", None)),
    ("main.handle_action", getattr(main, "handle_action", None)),
    ("main.handle_web", getattr(main, "handle_web", None)),
    ("main.handle_memory", getattr(main, "handle_memory", None)),
]

chat_module = getattr(main, "chat_module", None)

if chat_module is not None:
    TARGETS.extend([
        (
            "chat.handle_chat",
            getattr(chat_module, "handle_chat", None),
        ),
        (
            "chat.chat",
            getattr(chat_module, "chat", None),
        ),
    ])


def inspect_target(name, obj):
    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    if obj is None:
        print("[MISSING]")
        return

    print("TYPE:", type(obj))
    print("SIGNATURE:")

    try:
        print(inspect.signature(obj))
    except Exception as exc:
        print("[SIGNATURE ERROR]", exc)

    print()
    print("SOURCE:")

    try:
        source = inspect.getsource(obj)
        print(source)

        lower = source.lower()

        english_markers = [
            "you are",
            "assistant",
            "help you",
            "how can i help",
            "sure!",
            "let me help",
            "what would you like",
            "hello",
            "hi!",
            "today",
        ]

        found = [
            marker
            for marker in english_markers
            if marker in lower
        ]

        if found:
            print()
            print(
                "[WARNING] ENGLISH MARKERS:",
                found,
            )

    except Exception as exc:
        print(
            "[SOURCE ERROR]",
            repr(exc),
        )


print()
print("=" * 80)
print("MINH MINI — LANGUAGE SOURCE INSPECTION")
print("=" * 80)

for name, obj in TARGETS:
    inspect_target(
        name,
        obj,
    )

print()
print("=" * 80)
print("MODULES")
print("=" * 80)

for name in (
    "brain_module",
    "router_guard",
    "response_guard",
    "execution_controller",
    "chat_module",
):
    module = getattr(main, name, None)

    print(
        name,
        "->",
        module,
    )

print()
print("=" * 80)
print("INSPECTION COMPLETE")
print("=" * 80)