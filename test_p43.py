from brain import BrainCore
from think_x import ThinkXCore
from meta_orchestrator import MetaOrchestrator
from execution_contract import ExecutionContractBuilder

print("=== P4-3 EXECUTION CONTRACT TEST ===")

brain = BrainCore()
think_x = ThinkXCore()
meta = MetaOrchestrator()
builder = ExecutionContractBuilder()

tests = [
    "mở youtube",
    "tìm giá iphone",
    "nhớ Lam đang học Python",
    "mở",
    "nay là ngày bao nhiêu",
]

for message in tests:
    print("\n" + "=" * 60)
    print("INPUT:", message)

    brain_result = brain.think(message)
    think_result = think_x.think(
        message,
        brain_result,
    )
    meta_result = meta.orchestrate(
        message,
        brain_result,
        think_result,
    )
    contract = builder.build(
        message,
        meta_result,
    )

    data = contract.to_dict()

    print("META MODE:", meta_result.mode)
    print("META NEXT:", meta_result.next_step)
    print("CONTRACT ALLOWED:", data["allowed"])
    print("CONTRACT MODE:", data["mode"])
    print("CONTRACT TOOL:", data["tool"])
    print("CONTRACT OPERATION:", data["operation"])
    print("CONTRACT TARGET:", data["target"])
    print("VERIFY REQUIRED:", data["verify_required"])
    print("BLOCKERS:", data["blockers"])
    print("STEPS:", data["steps"])

print("\n" + "=" * 60)
print("VERSION:", builder.VERSION)
print("P4-3 TEST = DONE")
