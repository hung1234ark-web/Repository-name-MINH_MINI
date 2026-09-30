import inspect
import main


print("=" * 70)
print("MINH MINI - BUILD HANDLERS INSPECTION")
print("=" * 70)

print()
print("SOURCE FILE:")
print(main.__file__)

print()
print("=== build_handlers() SOURCE ===")
print()

try:
    source = inspect.getsource(main.build_handlers)
    print(source)
except Exception as exc:
    print("[FAIL] Không lấy được source build_handlers()")
    print(type(exc).__name__, exc)
    raise SystemExit(1)

print()
print("=" * 70)
print(">>> BUILD HANDLERS INSPECTION COMPLETE")
print("=" * 70)