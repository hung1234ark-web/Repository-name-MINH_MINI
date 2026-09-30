import inspect
import brain


def show(name):
    obj = getattr(brain, name, None)

    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    if obj is None:
        print("KHONG TON TAI")
        return

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


for name in [
    "detect_intent",
    "extract_action",
    "merge_context",
    "scan_history_context",
    "think",
]:
    show(name)


print("\n" + "=" * 80)
print("BRAIN DECISION TEST — KHONG SUA DU LIEU")
print("=" * 80)

try:
    result = brain.think("MẤY H RỒI")
    print("\n[MẤY H RỒI]")
    print(result)
except Exception as exc:
    print("TIME TEST ERROR:", type(exc).__name__, exc)

try:
    result = brain.think("TRUY CẬP GG")
    print("\n[TRUY CẬP GG]")
    print(result)
except Exception as exc:
    print("GOOGLE TEST ERROR:", type(exc).__name__, exc)

try:
    result = brain.think("tìm giá iPhone")
    print("\n[TÌM GIÁ IPHONE]")
    print(result)
except Exception as exc:
    print("WEB TEST ERROR:", type(exc).__name__, exc)

try:
    result = brain.think("nhớ Lam đang học Python")
    print("\n[MEMORY TEST]")
    print(result)
except Exception as exc:
    print("MEMORY TEST ERROR:", type(exc).__name__, exc)

print("\n>>> BRAIN DECISION FLOW INSPECT DONE")