from copy import deepcopy
from typing import Any, Dict, Optional


class CombinedEvaluation:
    """
    P9-4 Combined Evaluation Core

    Tổng hợp kết quả từ:
    - Critic
    - Red Team
    - FactCheck

    Phạm vi:
    - Chỉ đánh giá và tổng hợp kết quả.
    - Không execution.
    - Không routing.
    - Không Ollama.
    - Không Web.
    - Không Action.
    - Không mutate World Model.
    - Không mutate State Manager.
    """

    VERSION = "P9-4.0"

    VALID_VERDICTS = {"pass", "review", "block"}

    def __init__(self) -> None:
        self.last_result: Optional[Dict[str, Any]] = None

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return deepcopy(value)

        if hasattr(value, "__dict__"):
            try:
                return deepcopy(vars(value))
            except Exception:
                return {}

        return {}

    @staticmethod
    def _normalize_verdict(value: Any) -> str:
        verdict = str(value or "").strip().lower()

        if verdict in CombinedEvaluation.VALID_VERDICTS:
            return verdict

        return "review"

    @staticmethod
    def _score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(0.0, min(1.0, score))

    # =========================================================
    # INPUT CHECK
    # =========================================================

    def _check_input(
        self,
        critic_result: Dict[str, Any],
        red_team_result: Dict[str, Any],
        fact_check_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        issues = []
        warnings = []

        checks = {
            "critic_present": bool(critic_result),
            "red_team_present": bool(red_team_result),
            "fact_check_present": bool(fact_check_result),
        }

        if not critic_result:
            warnings.append("missing_critic_result")

        if not red_team_result:
            warnings.append("missing_red_team_result")

        if not fact_check_result:
            warnings.append("missing_fact_check_result")

        if not any(checks.values()):
            issues.append("no_evaluation_results")

        return {
            "checks": checks,
            "issues": issues,
            "warnings": warnings,
        }

    # =========================================================
    # VERDICT AGGREGATION
    # =========================================================

    def _combine_verdicts(
        self,
        critic_verdict: str,
        red_team_verdict: str,
        fact_check_verdict: str,
    ) -> str:

        verdicts = [
            critic_verdict,
            red_team_verdict,
            fact_check_verdict,
        ]

        # Một block là đủ để Combined Evaluation block.
        if "block" in verdicts:
            return "block"

        # Nếu không block nhưng có review,
        # kết quả chung cần review.
        if "review" in verdicts:
            return "review"

        return "pass"

    # =========================================================
    # SCORE
    # =========================================================

    def _combine_score(
        self,
        critic_result: Dict[str, Any],
        red_team_result: Dict[str, Any],
        fact_check_result: Dict[str, Any],
    ) -> float:

        scores = []

        for result in (
            critic_result,
            red_team_result,
            fact_check_result,
        ):
            if not result:
                continue

            if "score" in result:
                scores.append(self._score(result.get("score")))

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores), 4)

    # =========================================================
    # ISSUE / WARNING MERGE
    # =========================================================

    @staticmethod
    def _merge_messages(
        critic_result: Dict[str, Any],
        red_team_result: Dict[str, Any],
        fact_check_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        issues = []
        warnings = []

        sources = (
            ("critic", critic_result),
            ("red_team", red_team_result),
            ("fact_check", fact_check_result),
        )

        for source_name, result in sources:
            if not isinstance(result, dict):
                continue

            source_issues = result.get("issues", [])
            source_warnings = result.get("warnings", [])

            if isinstance(source_issues, list):
                for issue in source_issues:
                    issues.append({
                        "source": source_name,
                        "item": deepcopy(issue),
                    })

            if isinstance(source_warnings, list):
                for warning in source_warnings:
                    warnings.append({
                        "source": source_name,
                        "item": deepcopy(warning),
                    })

        return {
            "issues": issues,
            "warnings": warnings,
        }

    # =========================================================
    # MAIN EVALUATION
    # =========================================================

    def evaluate(
        self,
        critic_result: Any = None,
        red_team_result: Any = None,
        fact_check_result: Any = None,
    ) -> Dict[str, Any]:

        critic = self._as_dict(critic_result)
        red_team = self._as_dict(red_team_result)
        fact_check = self._as_dict(fact_check_result)

        input_check = self._check_input(
            critic,
            red_team,
            fact_check,
        )

        critic_verdict = self._normalize_verdict(
            critic.get("verdict")
        )

        red_team_verdict = self._normalize_verdict(
            red_team.get("verdict")
        )

        fact_check_verdict = self._normalize_verdict(
            fact_check.get("verdict")
        )

        # Nếu một module hoàn toàn không có kết quả,
        # không giả định nó PASS.
        available_count = sum(
            bool(result)
            for result in (
                critic,
                red_team,
                fact_check,
            )
        )

        if available_count == 0:
            verdict = "block"
            reason = "No evaluation result is available."
        else:
            verdict = self._combine_verdicts(
                critic_verdict if critic else "review",
                red_team_verdict if red_team else "review",
                fact_check_verdict if fact_check else "review",
            )

            if verdict == "block":
                reason = "At least one evaluator returned block."
            elif verdict == "review":
                reason = "At least one evaluator requires review."
            else:
                reason = "All available evaluators returned pass."

        score = self._combine_score(
            critic,
            red_team,
            fact_check,
        )

        messages = self._merge_messages(
            critic,
            red_team,
            fact_check,
        )

        issues = list(messages["issues"])
        warnings = list(messages["warnings"])

        issues.extend(input_check["issues"])
        warnings.extend(input_check["warnings"])

        result = {
            "verdict": verdict,
            "valid": verdict in self.VALID_VERDICTS,
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "checks": {
                "input": input_check["checks"],
                "critic_verdict": critic_verdict if critic else None,
                "red_team_verdict": red_team_verdict if red_team else None,
                "fact_check_verdict": fact_check_verdict if fact_check else None,
                "available_evaluators": available_count,
            },
            "critic": deepcopy(critic),
            "red_team": deepcopy(red_team),
            "fact_check": deepcopy(fact_check),
            "reason": reason,
            "version": self.VERSION,
        }

        self.last_result = deepcopy(result)

        return result

    # =========================================================
    # STATE API
    # =========================================================

    def get_last_result(self) -> Optional[Dict[str, Any]]:
        return deepcopy(self.last_result)

    def reset(self) -> None:
        self.last_result = None

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> Dict[str, Any]:
        errors = []

        if self.VERSION != "P9-4.0":
            errors.append("invalid_version")

        if not isinstance(self.VALID_VERDICTS, set):
            errors.append("invalid_verdict_definition")

        if self.last_result is not None:
            if not isinstance(self.last_result, dict):
                errors.append("invalid_last_result")

            else:
                verdict = self.last_result.get("verdict")

                if verdict not in self.VALID_VERDICTS:
                    errors.append("invalid_last_verdict")

                if not isinstance(
                    self.last_result.get("valid"),
                    bool,
                ):
                    errors.append("invalid_valid_flag")

        return {
            "valid": not errors,
            "errors": errors,
            "version": self.VERSION,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "valid": self.validate()["valid"],
            "has_result": self.last_result is not None,
            "last_verdict": (
                self.last_result.get("verdict")
                if isinstance(self.last_result, dict)
                else None
            ),
        }


# =============================================================
# FACTORY
# =============================================================

def create_combined_evaluation() -> CombinedEvaluation:
    return CombinedEvaluation()


# =============================================================
# SELF CHECK
# =============================================================

def self_check() -> Dict[str, Any]:
    evaluator = create_combined_evaluation()

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
        "score": 0.85,
        "issues": [],
        "warnings": [],
    }

    fact_check = {
        "verdict": "pass",
        "valid": True,
        "score": 0.95,
        "issues": [],
        "warnings": [],
    }

    result = evaluator.evaluate(
        critic_result=critic,
        red_team_result=red_team,
        fact_check_result=fact_check,
    )

    structure_ok = all(
        key in result
        for key in (
            "verdict",
            "valid",
            "score",
            "issues",
            "warnings",
            "checks",
            "critic",
            "red_team",
            "fact_check",
            "reason",
            "version",
        )
    )

    expected_pass = result.get("verdict") == "pass"
    validation_ok = evaluator.validate().get("valid") is True

    return {
        "version": evaluator.VERSION,
        "verdict": result.get("verdict"),
        "valid": (
            result.get("valid") is True
            and structure_ok
            and expected_pass
            and validation_ok
        ),
        "structure_ok": structure_ok,
        "expected_pass": expected_pass,
        "validation_ok": validation_ok,
    }


if __name__ == "__main__":
    print("=== P9-4 COMBINED EVALUATION CORE SELF CHECK ===")

    result = self_check()

    print(f"VERSION: {result['version']}")
    print(f"VERDICT: {result['verdict']}")
    print(f"VALID: {result['valid']}")

    if result["valid"]:
        print("P9-4 COMBINED EVALUATION CORE: PASS")
    else:
        print("P9-4 COMBINED EVALUATION CORE: FAIL")
