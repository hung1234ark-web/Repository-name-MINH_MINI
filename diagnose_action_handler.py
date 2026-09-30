# -*- coding: utf-8 -*-

import inspect
import action


print("=" * 70)
print("MINH MINI — ACTION HANDLER DIAGNOSTIC")
print("=" * 70)

handler = getattr(action, "handle_action_command", None)

if handler is None:
    print("[FAIL] Không tìm thấy action.handle_action_command")
    raise SystemExit(1)

print()
print("CALLABLE:")
print(handler)

print()
print("SIGNATURE:")
try:
    print(inspect.signature(handler))
except Exception as exc:
    print(f"[ERROR] {type(exc).__name__}: {exc}")

print()
print("PARAMETERS:")

try:
    sig = inspect.signature(handler)

    for name, param in sig.parameters.items():
        print(
            f"- {name}: "
            f"kind={param.kind} "
            f"default={param.default!r} "
            f"annotation={param.annotation!r}"
        )

except Exception as exc:
    print(f"[ERROR] {type(exc).__name__}: {exc}")

print()
print("MODULE:")
print(getattr(handler, "__module__", ""))

print()
print("QUALNAME:")
print(getattr(handler, "__qualname__", ""))

print()
print("SOURCE FILE:")

try:
    print(inspect.getsourcefile(handler))
except Exception as exc:
    print(f"[ERROR] {type(exc).__name__}: {exc}")

print()
print("SOURCE:")

try:
    print(inspect.getsource(handler))
except Exception as exc:
    print(f"[ERROR] {type(exc).__name__}: {exc}")

print()
print("=" * 70)
print("END DIAGNOSTIC")
print("=" * 70)