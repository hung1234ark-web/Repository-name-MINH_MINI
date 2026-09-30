import main

print("=== P4-4 RUNTIME REGRESSION ===")

app = main.MINH

tests = [
    "mở youtube",
    "tìm giá iphone",
    "nhớ Lam đang học Python",
    "mở",
    "nay là ngày bao nhiêu",
]

for message in tests:
    print("\n" + "=" * 70)
    print("INPUT:", message)

    try:
        output = app.process(message)

        print("OUTPUT:", output)

        contract = getattr(
            app,
            "last_execution_contract",
            None,
        )

        if contract is None:
            print("CONTRACT: NONE")
            continue

        data = contract.to_dict()

        print("CONTRACT ALLOWED:", data["allowed"])
        print("CONTRACT MODE:", data["mode"])
        print("CONTRACT TOOL:", data["tool"])
        print("CONTRACT OPERATION:", data["operation"])
        print("CONTRACT TARGET:", data["target"])
        print("BLOCKERS:", data["blockers"])
        print("VERIFY REQUIRED:", data["verify_required"])

        if message == "mở youtube":
            assert data["allowed"] is True
            assert data["tool"] == "action"
            assert data["operation"] == "open"
            assert data["target"] == "youtube"

        elif message == "tìm giá iphone":
            assert data["allowed"] is True
            assert data["tool"] == "web"
            assert data["operation"] == "search"

        elif message == "nhớ Lam đang học Python":
            assert data["allowed"] is True
            assert data["tool"] == "memory"
            assert data["operation"] == "memory"

        elif message == "mở":
            assert data["allowed"] is False
            assert data["mode"] == "blocked"
            assert "missing_target" in data["blockers"]

        elif message == "nay là ngày bao nhiêu":
            assert data["allowed"] is True
            assert data["tool"] == "system_date"
            assert data["operation"] == "read_date"

        print("TEST CASE: PASS")

    except Exception as exc:
        print("TEST CASE: FAIL")
        print("ERROR:", repr(exc))

print("\n" + "=" * 70)
print("P4-4 RUNTIME REGRESSION = DONE")
