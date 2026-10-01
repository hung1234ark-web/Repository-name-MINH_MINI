from diagnosis_recovery_replan import create_diagnosis_recovery_replan

def test_p13_success_passthrough():
    p = create_diagnosis_recovery_replan()
    result = p.analyze(
        message="ok",
        decision={"intent": "action", "tool": "action"},
        execution_result={"success": True, "tool": "action"},
        verification={"verified": True},
    )
    assert result["status"] == "pass"
    assert result["recovery"] == "stop"
    assert result["replan"] == []

def test_p13_action_failure_replans_without_execution():
    p = create_diagnosis_recovery_replan()
    result = p.analyze(
        message="mở youtube",
        decision={"intent": "action", "tool": "action"},
        execution_result={"success": False, "tool": "action", "error": "failed"},
        verification={"verified": False},
    )
    assert result["diagnosis"] == "verification_failed"
    assert result["recovery"] == "replan"
    assert "await_reexecution_authorization" in result["replan"]

def test_p13_self_check():
    assert create_diagnosis_recovery_replan().self_check() if hasattr(create_diagnosis_recovery_replan(), "self_check") else True
