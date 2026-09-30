import main

print("=== P4-2 META-ORCHESTRATOR REAL TEST ===")

app = main.MINH

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

    try:
        output = app.process(message)

        print("OUTPUT:", output)

        meta = getattr(
            app,
            "last_meta_orchestration",
            None,
        )

        if meta is None:
            print("META RESULT: NONE")
            print("STATUS: FAIL")
            continue

        if hasattr(meta, "to_dict"):
            data = meta.to_dict()
        else:
            data = meta

        print("META MODE:", data.get("mode"))
        print("META NEXT:", data.get("next_step"))
        print("META TOOL:", data.get("tool"))
        print("META INTENT:", data.get("intent"))
        print("META PLAN:", data.get("plan"))
        print("META STATUS: PASS")

    except Exception as exc:
        print("RUNTIME ERROR:", repr(exc))
        print("STATUS: FAIL")

print("\n" + "=" * 60)

meta = getattr(
    app,
    "last_meta_orchestration",
    None,
)

if meta is not None:
    print("LAST META RESULT = PASS")
else:
    print("LAST META RESULT = FAIL")

print("P4-2 REAL TEST = DONE")
