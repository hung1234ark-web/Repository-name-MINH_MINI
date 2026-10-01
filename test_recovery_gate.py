"""P13-2 Recovery Gate tests."""
from recovery_gate import create_recovery_gate


def run_tests() -> dict:
    gate = create_recovery_gate()

    cases = {
        "missing": gate.evaluate(None),
        "clarify": gate.evaluate({
            "status": "review",
            "diagnosis": "missing_information",
            "recovery": "clarify",
            "replan": ["request_missing_information"],
        }),
        "replan": gate.evaluate({
            "status": "review",
            "diagnosis": "verification_failed",
            "recovery": "replan",
            "replan": ["adjust_plan"],
        }),
        "reselect": gate.evaluate({
            "status": "review",
            "diagnosis": "tool_missing",
            "recovery": "reselect_tool",
            "replan": ["reselect_tool"],
        }),
        "pass": gate.evaluate({
            "status": "pass",
            "diagnosis": "no_failure_detected",
            "recovery": "stop",
            "replan": [],
        }),
    }

    checks = {
        "self_check": gate.validate()["valid"] is True,
        "missing_stops": cases["missing"]["decision"] == "stop",
        "clarify_blocks": (
            cases["clarify"]["decision"] == "clarify"
            and cases["clarify"]["allowed_to_execute"] is False
        ),
        "replan_blocks": (
            cases["replan"]["decision"] == "replan"
            and cases["replan"]["allowed_to_execute"] is False
        ),
        "reselect_blocks": (
            cases["reselect"]["decision"] == "reselect_tool"
            and cases["reselect"]["allowed_to_execute"] is False
        ),
        "pass_proceeds": (
            cases["pass"]["decision"] == "proceed"
            and cases["pass"]["allowed_to_execute"] is True
        ),
    }

    return {"valid": all(checks.values()), "checks": checks, "cases": cases}


if __name__ == "__main__":
    print(run_tests())
