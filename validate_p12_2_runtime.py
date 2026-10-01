import main

print("=" * 90)
print("P12-2 FINAL RUNTIME BRIDGE VALIDATION")
print("NO WEB / NO OLLAMA / NO ACTION")
print("=" * 90)

runtime = getattr(main, "MINH", None)

if runtime is None:
    raise SystemExit("GLOBAL MINH MISSING")

print("GLOBAL MINH: PASS")
print("TYPE:", type(runtime).__name__)

helper = getattr(
    runtime,
    "_p12_2_prepare_tool_selection",
    None,
)

if not callable(helper):
    raise SystemExit(
        "P12-2 HELPER MISSING"
    )

print("P12-2 HELPER: PASS")

tests = [
    (
        "WEB",
        "tìm thông tin trên web",
        {
            "intent": "web",
            "tool": "web",
        },
    ),
    (
        "MEMORY",
        "hãy nhớ điều này",
        {
            "intent": "memory",
            "tool": "memory",
        },
    ),
    (
        "TIME",
        "bây giờ là mấy giờ",
        {
            "intent": "time",
            "tool": "time",
        },
    ),
    (
        "ACTION",
        "mở ứng dụng",
        {
            "intent": "action",
            "tool": "action",
        },
    ),
]

print("\n=== BRIDGE TESTS ===")

for name, message, decision in tests:

    result = helper(
        message=message,
        decision=decision,
        result={
            "judge": {
                "decision": "proceed",
            }
        },
    )

    print("\nTEST:", name)
    print("MESSAGE:", message)
    print("DECISION TOOL:", result.get("decision_tool"))
    print("SELECTED TOOL:", result.get("tool"))
    print("TOOL MATCH:", result.get("tool_match"))
    print("ADVISORY ONLY:", result.get("advisory_only"))

    if result.get("decision_tool") != decision["tool"]:
        raise SystemExit(
            f"{name}: decision tool changed"
        )

    if result.get("tool") != decision["tool"]:
        raise SystemExit(
            f"{name}: selector mismatch: "
            f"{result.get('tool')!r}"
        )

    if result.get("tool_match") is not True:
        raise SystemExit(
            f"{name}: tool_match != True"
        )

    if result.get("advisory_only") is not True:
        raise SystemExit(
            f"{name}: advisory_only contract failed"
        )

    print(name, ": PASS")

print("\n=== STATE SAVE ===")

saved = getattr(
    runtime,
    "last_p11_tool_selection",
    None,
)

if not isinstance(saved, dict):
    raise SystemExit(
        "P11 STATE SAVE FAILED"
    )

print("LAST P11 TOOL:", saved.get("tool"))
print("STATE SAVE: PASS")

print("\n=== EXECUTION SAFETY ===")

print(
    "This validation calls only "
    "_p12_2_prepare_tool_selection()."
)
print("No execute_decision() called.")
print("No Web called.")
print("No Ollama called.")
print("No Action called.")

print("EXECUTION SAFETY: PASS")

print("\n" + "=" * 90)
print("P12-2 FINAL RUNTIME BRIDGE VALIDATION: PASS")
print("JUDGE -> TOOL SELECTOR: PASS")
print("WEB -> WEB: PASS")
print("MEMORY -> MEMORY: PASS")
print("TIME -> TIME: PASS")
print("ACTION -> ACTION: PASS")
print("ADVISORY ONLY: PASS")
print("STATE SAVE: PASS")
print("NO EXECUTION: PASS")
print("=" * 90)
