"""MINH MINI P13-2 runtime validation.

Validates the P13-1 -> Recovery Gate contract and the main.py integration
without executing any external tool, Web, Ollama, or Action.
"""

from diagnosis_recovery_replan import create_diagnosis_recovery_replan
from recovery_gate import create_recovery_gate


def run_tests() -> dict:
    p13 = create_diagnosis_recovery_replan()
    gate = create_recovery_gate()

    success = p13.analyze(
        message="ok",
        decision={"intent": "action", "tool": "action"},
        execution_result={"success": True, "tool": "action"},
        verification={"verified": True},
    )
    success_gate = gate.evaluate(success)

    failure = p13.analyze(
        message="mở youtube",
        decision={"intent": "action", "tool": "action"},
        execution_result={
            "success": False,
            "tool": "action",
            "error": "failed",
        },
        verification={"verified": False},
    )
    failure_gate = gate.evaluate(failure)

    checks = {
        "p13_self_check": p13.validate()["valid"] is True,
        "gate_self_check": gate.validate()["valid"] is True,
        "success_to_proceed": (
            success["status"] == "pass"
            and success_gate["decision"] == "proceed"
            and success_gate["allowed_to_execute"] is True
        ),
        "failure_to_replan": (
            failure["recovery"] == "replan"
            and failure_gate["decision"] == "replan"
            and failure_gate["allowed_to_execute"] is False
        ),
        "replan_contains_authorization": (
            "await_reexecution_authorization" in failure["replan"]
        ),
        "gate_never_executes": (
            gate.evaluate(failure)["decision"] == "replan"
        ),
    }

    return {
        "valid": all(checks.values()),
        "checks": checks,
        "success": success,
        "success_gate": success_gate,
        "failure": failure,
        "failure_gate": failure_gate,
    }


def run_main_integration_check() -> dict:
    import main

    instance = main.MINH

    checks = {
        "p13_recovery_present": getattr(instance, "p13_recovery", None) is not None,
        "p13_gate_present": getattr(instance, "p13_recovery_gate", None) is not None,
        "p13_result_slot_present": hasattr(instance, "last_p13_result"),
        "p13_gate_slot_present": hasattr(instance, "last_p13_recovery_gate"),
    }

    return {
        "valid": all(checks.values()),
        "checks": checks,
    }


if __name__ == "__main__":
    result = run_tests()
    print("P13-2 MODULE RUNTIME:", result)

    integration = run_main_integration_check()
    print("P13-2 MAIN INTEGRATION:", integration)

    print("P13-2 RUNTIME VALID:", result["valid"] and integration["valid"])
