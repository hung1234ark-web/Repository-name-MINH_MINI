"""Regression test for the P13-2 execution boundary."""


def run_test() -> dict:
    import main

    instance = main.MINH
    original_controller = instance.controller
    calls = []

    class FakeController:
        def execute(self, message, decision):
            calls.append((message, decision))
            return {"success": True, "tool": "fake", "answer": "EXECUTED"}

    try:
        instance.controller = FakeController()
        instance.last_p13_recovery_gate = {
            "decision": "replan",
            "action_required": "apply_replan_after_new_authorization",
            "allowed_to_execute": False,
            "reason": "verification_failed",
            "checks": [],
            "version": "P13-2.1",
        }

        answer, result = instance.execute_decision(
            "mở youtube",
            {"intent": "action", "tool": "action"},
        )

        blocked = (
            answer == ""
            and result.get("execution_blocked") is True
            and result.get("tool") == "recovery_gate"
            and calls == []
        )
        return {
            "valid": blocked,
            "blocked": blocked,
            "controller_calls": len(calls),
            "result": result,
        }
    finally:
        instance.controller = original_controller
        instance.last_p13_recovery_gate = None


if __name__ == "__main__":
    result = run_test()
    print("P13-2 EXECUTION BOUNDARY:", result)
    print("P13-2 EXECUTION BOUNDARY VALID:", result["valid"])
