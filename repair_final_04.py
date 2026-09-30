from pathlib import Path
import inspect
import execution_controller


print("=" * 70)
print("REPAIR FINAL 04 — INSPECT EXECUTION CONTROLLER")
print("=" * 70)

Controller = execution_controller.ExecutionController

print("\n=== CLASS ===")
print(Controller)

print("\n=== __init__ SIGNATURE ===")
print(inspect.signature(Controller.__init__))

print("\n=== execute SIGNATURE ===")
print(inspect.signature(Controller.execute))

print("\n=== _call_handler SIGNATURE ===")
print(inspect.signature(Controller._call_handler))

print("\n=== _call_handler SOURCE ===")
try:
    print(inspect.getsource(Controller._call_handler))
except Exception as e:
    print("KHONG DOC DUOC SOURCE:", repr(e))

print("\n=== execute SOURCE ===")
try:
    print(inspect.getsource(Controller.execute))
except Exception as e:
    print("KHONG DOC DUOC SOURCE:", repr(e))

print("\n=== NORMALIZE SOURCE ===")
if hasattr(execution_controller, "normalize_handler_result"):
    try:
        print(inspect.getsource(
            execution_controller.normalize_handler_result
        ))
    except Exception as e:
        print("KHONG DOC DUOC SOURCE:", repr(e))
else:
    print("Khong co normalize_handler_result")

print("\n" + "=" * 70)
print("REPAIR 04 HOAN TAT")
print("=" * 70)