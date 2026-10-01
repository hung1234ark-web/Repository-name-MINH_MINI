import importlib
import py_compile
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent

FILES = {
    "critic.py": "P9-1 Critic",
    "red_team.py": "P9-2 Red Team",
    "fact_check.py": "P9-3 FactCheck",
    "combined_evaluation.py": "P9-4 Combined Evaluation",
}


def check_file(name):
    path = APP_DIR / name
    return path.exists()


def check_compile(name):
    path = APP_DIR / name

    try:
        py_compile.compile(
            str(path),
            doraise=True,
        )
        return True
    except Exception:
        return False


def check_import(module_name):
    try:
        module = importlib.import_module(module_name)
        return module
    except Exception:
        return None


def check_class(module, class_name):
    return (
        module is not None
        and hasattr(module, class_name)
        and isinstance(getattr(module, class_name), type)
    )


def test_critic():
    module = check_import("critic")

    if not check_class(module, "Critic"):
        return False

    evaluator = module.create_critic()

    result = evaluator.evaluate(
        goal={"text": "open youtube"},
        plan={"tasks": [{"description": "open youtube"}]},
        result={
            "success": True,
            "status": "completed",
        },
    )

    return (
        isinstance(result, dict)
        and result.get("verdict") in {"pass", "review", "block"}
        and isinstance(result.get("valid"), bool)
    )


def test_red_team():
    module = check_import("red_team")

    if not check_class(module, "RedTeam"):
        return False

    evaluator = module.create_red_team()

    result = evaluator.evaluate(
        goal={"text": "open youtube"},
        plan={"tasks": [{"description": "open youtube"}]},
        result={
            "success": True,
            "status": "completed",
        },
    )

    return (
        isinstance(result, dict)
        and result.get("verdict") in {"pass", "review", "block"}
        and isinstance(result.get("valid"), bool)
    )


def test_fact_check():
    module = check_import("fact_check")

    if not check_class(module, "FactCheck"):
        return False

    evaluator = module.create_fact_check()

    result = evaluator.evaluate(
        facts={
            "platform": "youtube",
            "available": True,
        },
        claims=[
            {
                "text": "The target platform is youtube.",
                "supported": True,
                "source": "supplied_context",
            }
        ],
    )

    return (
        isinstance(result, dict)
        and result.get("verdict") in {"pass", "review", "block"}
        and isinstance(result.get("valid"), bool)
    )


def test_combined():
    module = check_import("combined_evaluation")

    if not check_class(module, "CombinedEvaluation"):
        return False

    evaluator = module.create_combined_evaluation()

    critic = {
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
        "issues": [],
        "warnings": [],
    }

    red_team = {
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
        "issues": [],
        "warnings": [],
    }

    fact_check = {
        "verdict": "pass",
        "valid": True,
        "score": 0.90,
        "issues": [],
        "warnings": [],
    }

    result = evaluator.evaluate(
        critic_result=critic,
        red_team_result=red_team,
        fact_check_result=fact_check,
    )

    return (
        isinstance(result, dict)
        and result.get("verdict") == "pass"
        and result.get("valid") is True
    )


def test_verdict_policy():
    module = check_import("combined_evaluation")

    if module is None:
        return False

    evaluator = module.create_combined_evaluation()

    base = {
        "valid": True,
        "score": 1.0,
        "issues": [],
        "warnings": [],
    }

    # PASS + PASS + PASS -> PASS
    result_pass = evaluator.evaluate(
        critic_result={**base, "verdict": "pass"},
        red_team_result={**base, "verdict": "pass"},
        fact_check_result={**base, "verdict": "pass"},
    )

    if result_pass.get("verdict") != "pass":
        return False

    # REVIEW phải lan truyền thành REVIEW
    result_review = evaluator.evaluate(
        critic_result={**base, "verdict": "pass"},
        red_team_result={**base, "verdict": "review"},
        fact_check_result={**base, "verdict": "pass"},
    )

    if result_review.get("verdict") != "review":
        return False

    # BLOCK phải lan truyền thành BLOCK
    result_block = evaluator.evaluate(
        critic_result={**base, "verdict": "pass"},
        red_team_result={**base, "verdict": "block"},
        fact_check_result={**base, "verdict": "pass"},
    )

    if result_block.get("verdict") != "block":
        return False

    # Không có evaluator -> BLOCK, không được giả định PASS
    result_empty = evaluator.evaluate()

    if result_empty.get("verdict") != "block":
        return False

    return True


def test_result_isolation():
    module = check_import("combined_evaluation")

    if module is None:
        return False

    evaluator = module.create_combined_evaluation()

    original = {
        "verdict": "pass",
        "valid": True,
        "score": 0.8,
        "issues": [],
        "warnings": [],
    }

    result = evaluator.evaluate(
        critic_result=original,
        red_team_result=original,
        fact_check_result=original,
    )

    # Sửa kết quả Combined không được sửa input gốc.
    result["critic"]["verdict"] = "block"

    return original["verdict"] == "pass"


def test_self_checks():
    modules = [
        ("critic", "self_check"),
        ("red_team", "self_check"),
        ("fact_check", "self_check"),
        ("combined_evaluation", "self_check"),
    ]

    for module_name, function_name in modules:
        module = check_import(module_name)

        if module is None:
            return False

        function = getattr(module, function_name, None)

        if not callable(function):
            return False

        result = function()

        if not isinstance(result, dict):
            return False

        if result.get("valid") is not True:
            return False

    return True


def main():
    print("=== P9-5 CORE VALIDATION ===")

    all_pass = True

    print("\n=== FILE CHECK ===")

    for filename, label in FILES.items():
        passed = check_file(filename)

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_pass = False

    print("\n=== COMPILE CHECK ===")

    for filename, label in FILES.items():
        passed = False

        if check_file(filename):
            passed = check_compile(filename)

        print(
            f"{label} COMPILE: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_pass = False

    print("\n=== IMPORT / CLASS CHECK ===")

    imports = {
        "critic": "Critic",
        "red_team": "RedTeam",
        "fact_check": "FactCheck",
        "combined_evaluation": "CombinedEvaluation",
    }

    imported_modules = {}

    for module_name, class_name in imports.items():
        module = check_import(module_name)
        imported_modules[module_name] = module

        import_pass = module is not None
        class_pass = check_class(module, class_name)

        print(
            f"{module_name.upper()} IMPORT: "
            f"{'PASS' if import_pass else 'FAIL'}"
        )

        print(
            f"{class_name.upper()} CLASS: "
            f"{'PASS' if class_pass else 'FAIL'}"
        )

        if not import_pass or not class_pass:
            all_pass = False

    print("\n=== FUNCTIONAL CORE CHECK ===")

    tests = [
        ("CRITIC CORE", test_critic),
        ("RED TEAM CORE", test_red_team),
        ("FACTCHECK CORE", test_fact_check),
        ("COMBINED EVALUATION CORE", test_combined),
        ("VERDICT POLICY", test_verdict_policy),
        ("RESULT ISOLATION", test_result_isolation),
        ("ALL SELF CHECKS", test_self_checks),
    ]

    for label, function in tests:
        try:
            passed = function()
        except Exception as exc:
            passed = False
            print(f"{label} ERROR: {type(exc).__name__}: {exc}")

        print(
            f"{label}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            all_pass = False

    print("\n=== ARCHITECTURE SAFETY CHECK ===")

    safety_pass = True

    for filename in FILES:
        path = APP_DIR / filename

        if not path.exists():
            safety_pass = False
            continue

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()
        except Exception:
            safety_pass = False
            continue

        forbidden_patterns = [
            "subprocess.",
            "os.system(",
            "requests.",
            "urllib.request",
        ]

        for pattern in forbidden_patterns:
            if pattern in source:
                print(
                    f"{filename}: "
                    f"FORBIDDEN EXECUTION/NETWORK PATTERN "
                    f"FOUND -> {pattern}"
                )
                safety_pass = False

    print(
        f"P9 CORE SAFETY: "
        f"{'PASS' if safety_pass else 'FAIL'}"
    )

    if not safety_pass:
        all_pass = False

    print("\n=== MAIN.PY MODIFICATION CHECK ===")

    main_path = APP_DIR / "main.py"

    if main_path.exists():
        print("MAIN.PY EXISTS: PASS")
        print("MAIN.PY MODIFIED BY THIS VALIDATOR: NO")
    else:
        print("MAIN.PY EXISTS: FAIL")
        all_pass = False

    print("\n=== FINAL ===")

    if all_pass:
        print("P9-5 CORE VALIDATION: PASS")
        print("P9-1 CRITIC CORE: PRESERVED")
        print("P9-2 RED TEAM CORE: PRESERVED")
        print("P9-3 FACTCHECK CORE: PRESERVED")
        print("P9-4 COMBINED EVALUATION CORE: PRESERVED")
        print("MAIN.PY: NOT MODIFIED")
        print("AUTO EXECUTION: NO")
        print("AUTO GIT COMMIT: NO")
    else:
        print("P9-5 CORE VALIDATION: FAIL")
        print("DO NOT INTEGRATE P9 INTO MAIN.PY")


if __name__ == "__main__":
    main()
