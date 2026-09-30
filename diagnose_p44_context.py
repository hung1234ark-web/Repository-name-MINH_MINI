import main

app = main.MINH

print("=== P4-4 CONTEXT DIAGNOSTIC ===")

message = "mở"

print("INPUT:", message)

# ------------------------------------------------------------
# Run normal processing
# ------------------------------------------------------------

output = app.process(message)

print("\nOUTPUT:", output)

# ------------------------------------------------------------
# THINK X
# ------------------------------------------------------------

think = getattr(app, "last_think_x", None)

print("\n--- THINK X ---")

if think is None:
    print("THINK X = NONE")
else:
    try:
        print("TYPE:", type(think).__name__)
        print("INTENT:", getattr(think, "intent", None))
        print("ACTION:", getattr(think, "action", None))
        print("TARGET:", getattr(think, "target", None))
        print("MISSING:", getattr(think, "missing", None))
        print(
            "REQUIRES_CLARIFICATION:",
            getattr(
                think,
                "requires_clarification",
                None,
            ),
        )
    except Exception as exc:
        print("THINK READ ERROR:", repr(exc))

# ------------------------------------------------------------
# META
# ------------------------------------------------------------

meta = getattr(
    app,
    "last_meta_orchestration",
    None,
)

print("\n--- META ---")

if meta is None:
    print("META = NONE")
else:
    try:
        print("TYPE:", type(meta).__name__)
        print("INTENT:", getattr(meta, "intent", None))
        print("ACTION:", getattr(meta, "action", None))
        print("TARGET:", getattr(meta, "target", None))
        print("MODE:", getattr(meta, "mode", None))
        print("NEXT:", getattr(meta, "next_step", None))
        print("TOOL:", getattr(meta, "tool", None))
        print(
            "CONSTRAINTS:",
            getattr(meta, "constraints", None),
        )
    except Exception as exc:
        print("META READ ERROR:", repr(exc))

# ------------------------------------------------------------
# CONTRACT
# ------------------------------------------------------------

contract = getattr(
    app,
    "last_execution_contract",
    None,
)

print("\n--- CONTRACT ---")

if contract is None:
    print("CONTRACT = NONE")
else:
    try:
        data = contract.to_dict()
        for key in [
            "allowed",
            "tool",
            "operation",
            "target",
            "mode",
            "blockers",
            "requirements",
            "steps",
            "reason",
        ]:
            print(
                key.upper() + ":",
                data.get(key),
            )
    except Exception as exc:
        print("CONTRACT READ ERROR:", repr(exc))

print("\n=== DIAGNOSTIC DONE ===")
