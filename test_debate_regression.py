from main import MINH

tests = [
    "/debate Có nên thêm một AI mới vào MINH MINI không?",
    "/debate Có nên dùng AI A hay AI B cho MINH MINI?",
    "/debate Có nên thay Ollama hiện tại không?",
    "/debate Có nên thêm một web tool mới không?",
]

print("=" * 60)
print("MINH MINI — DEBATE REGRESSION TEST")
print("=" * 60)

all_pass = True

for i, prompt in enumerate(tests, 1):
    print(f"\n--- TEST {i} ---")
    print("INPUT:", prompt)

    try:
        answer = MINH.process(prompt)

        status = MINH.status()

        checks = {
            "answer_present": bool(answer),
            "debate_enabled": status.get("debate") is True,
            "analysis_only": status.get("debate_mode") == "analysis_only",
            "execution_disabled": status.get("debate_execution") is False,
            "p45_not_started": MINH.last_execution_verification is None,
            "not_execution_handler": '"debate": handle_' not in open(
                "main.py",
                "r",
                encoding="utf-8"
            ).read(),
        }

        passed = all(checks.values())

        for name, result in checks.items():
            print(f"{name:24}: {'PASS' if result else 'FAIL'}")

        print("RESULT:", "PASS" if passed else "FAIL")

        if not passed:
            all_pass = False

    except Exception as exc:
        all_pass = False
        print("EXCEPTION:", repr(exc))
        print("RESULT: FAIL")

print("\n" + "=" * 60)
print("FINAL:", "PASS" if all_pass else "FAIL")
print("=" * 60)

if not all_pass:
    raise SystemExit(1)
