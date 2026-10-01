"""
MINH MINI - P9-3 FactCheck Core
Version: P9-3.0

Purpose:
    Deterministically inspect supplied facts/claims for
    completeness, consistency and explicit evidence status.

Design constraints:
    - No Web
    - No Ollama
    - No execution
    - No routing
    - No Action
    - No World Model mutation
    - No State Manager mutation
    - Read-only evaluation
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional


class FactCheck:
    VERSION = "P9-3.0"

    VALID_VERDICTS = {
        "pass",
        "review",
        "block",
    }

    def __init__(self) -> None:
        self.last_result: Optional[Dict[str, Any]] = None

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    # =========================================================
    # CLAIM CHECK
    # =========================================================

    def _check_claims(
        self,
        claims: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> List[Dict[str, Any]]:
        if claims is None:
            warnings.append("missing_claims")
            checks["claims_present"] = False
            return []

        if not isinstance(claims, list):
            issues.append("claims_not_list")
            checks["claims_present"] = False
            return []

        checks["claims_present"] = True

        if not claims:
            warnings.append("empty_claims")
            checks["claims_nonempty"] = False
            return []

        checks["claims_nonempty"] = True

        normalized: List[Dict[str, Any]] = []

        for index, claim in enumerate(claims):
            if isinstance(claim, str):
                text = claim.strip()

                if not text:
                    warnings.append(
                        f"claim_{index}_empty"
                    )
                    continue

                normalized.append(
                    {
                        "text": text,
                        "supported": None,
                        "source": None,
                    }
                )
                continue

            if not isinstance(claim, dict):
                issues.append(
                    f"invalid_claim_{index}"
                )
                continue

            text = self._text(
                claim.get("text")
                or claim.get("claim")
                or claim.get("statement")
            )

            if not text:
                warnings.append(
                    f"claim_{index}_missing_text"
                )
                continue

            normalized.append(
                {
                    "text": text,
                    "supported": claim.get(
                        "supported"
                    ),
                    "source": claim.get(
                        "source"
                    ),
                }
            )

        checks["claims_parseable"] = (
            len(normalized) > 0
        )

        return normalized

    # =========================================================
    # EVIDENCE CHECK
    # =========================================================

    def _check_evidence(
        self,
        claims: List[Dict[str, Any]],
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if not claims:
            checks["evidence_assessable"] = False
            return

        unsupported = 0
        unknown = 0
        supported = 0

        for claim in claims:
            value = claim.get(
                "supported"
            )

            if value is True:
                supported += 1
            elif value is False:
                unsupported += 1
            else:
                unknown += 1

        checks["supported_claims_present"] = (
            supported > 0
        )

        checks["unsupported_claims_present"] = (
            unsupported > 0
        )

        checks["unknown_claims_present"] = (
            unknown > 0
        )

        if unsupported:
            issues.append(
                "unsupported_claims"
            )

        if unknown:
            warnings.append(
                "unverified_claims"
            )

        checks["evidence_assessable"] = True

    # =========================================================
    # SOURCE CHECK
    # =========================================================

    def _check_sources(
        self,
        claims: List[Dict[str, Any]],
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if not claims:
            checks["sources_assessable"] = False
            return

        missing_sources = 0

        for claim in claims:
            source = claim.get("source")

            if source is None:
                missing_sources += 1
                continue

            if isinstance(source, str):
                if not source.strip():
                    missing_sources += 1
            elif not source:
                missing_sources += 1

        checks["sources_assessable"] = True

        if missing_sources:
            warnings.append(
                "claims_missing_sources"
            )
            checks["all_claims_have_sources"] = False
        else:
            checks["all_claims_have_sources"] = True

    # =========================================================
    # FACT STRUCTURE CHECK
    # =========================================================

    def _check_facts(
        self,
        facts: Any,
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        if facts is None:
            warnings.append("missing_facts")
            checks["facts_present"] = False
            return

        if not isinstance(facts, dict):
            issues.append("facts_not_dict")
            checks["facts_present"] = False
            return

        checks["facts_present"] = True

        if not facts:
            warnings.append("empty_facts")
            checks["facts_nonempty"] = False
        else:
            checks["facts_nonempty"] = True

    # =========================================================
    # CONSISTENCY CHECK
    # =========================================================

    def _check_consistency(
        self,
        facts: Any,
        claims: List[Dict[str, Any]],
        issues: List[str],
        warnings: List[str],
        checks: Dict[str, bool],
    ) -> None:
        facts_data = self._as_dict(facts)

        if not claims:
            checks["fact_claim_consistency"] = True
            return

        contradictions = 0

        for claim in claims:
            claim_key = self._text(
                claim.get("key")
            )

            if not claim_key:
                continue

            if claim_key not in facts_data:
                continue

            fact_value = facts_data.get(
                claim_key
            )

            expected = claim.get(
                "expected"
            )

            if expected is not None:
                if fact_value != expected:
                    contradictions += 1

        if contradictions:
            issues.append(
                "fact_claim_contradiction"
            )
            checks[
                "fact_claim_consistency"
            ] = False
        else:
            checks[
                "fact_claim_consistency"
            ] = True

    # =========================================================
    # VERDICT
    # =========================================================

    @staticmethod
    def _verdict(
        issues: List[str],
        warnings: List[str],
    ) -> str:
        blocking = {
            "claims_not_list",
            "invalid_claim_0",
            "facts_not_dict",
            "unsupported_claims",
            "fact_claim_contradiction",
        }

        if any(
            item in blocking
            for item in issues
        ):
            return "block"

        if issues or warnings:
            return "review"

        return "pass"

    # =========================================================
    # PUBLIC API
    # =========================================================

    def evaluate(
        self,
        facts: Any = None,
        claims: Any = None,
    ) -> Dict[str, Any]:
        """
        Evaluate supplied facts and claims.

        This module does not retrieve or verify information
        externally. It evaluates only supplied evidence metadata.
        """

        issues: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        self._check_facts(
            facts,
            issues,
            warnings,
            checks,
        )

        normalized_claims = self._check_claims(
            claims,
            issues,
            warnings,
            checks,
        )

        self._check_evidence(
            normalized_claims,
            issues,
            warnings,
            checks,
        )

        self._check_sources(
            normalized_claims,
            issues,
            warnings,
            checks,
        )

        self._check_consistency(
            facts,
            normalized_claims,
            issues,
            warnings,
            checks,
        )

        verdict = self._verdict(
            issues,
            warnings,
        )

        score = 1.0

        score -= min(
            0.15 * len(warnings),
            0.45,
        )

        score -= min(
            0.30 * len(issues),
            1.0,
        )

        score = max(
            0.0,
            min(1.0, score),
        )

        result = {
            "verdict": verdict,
            "valid": verdict != "block",
            "score": score,
            "issues": list(issues),
            "warnings": list(warnings),
            "checks": deepcopy(checks),
            "facts": deepcopy(facts),
            "claims": deepcopy(claims),
            "normalized_claims": deepcopy(
                normalized_claims
            ),
            "reason": (
                "Facts and claims passed structural checks."
                if verdict == "pass"
                else (
                    "Fact verification requires review."
                    if verdict == "review"
                    else "Fact-checking found a blocking issue."
                )
            ),
            "version": self.VERSION,
        }

        self.last_result = deepcopy(
            result
        )

        return deepcopy(result)

    def get_last_result(
        self,
    ) -> Optional[Dict[str, Any]]:
        if self.last_result is None:
            return None

        return deepcopy(
            self.last_result
        )

    def reset(self) -> None:
        self.last_result = None

    def validate(self) -> Dict[str, Any]:
        return {
            "valid": True,
            "version": self.VERSION,
            "last_result_present": (
                self.last_result is not None
            ),
            "supported_verdicts": sorted(
                self.VALID_VERDICTS
            ),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "valid": True,
            "last_result": deepcopy(
                self.last_result
            ),
        }


def create_fact_check() -> FactCheck:
    return FactCheck()


def self_check() -> Dict[str, Any]:
    checker = FactCheck()

    facts = {
        "platform": "youtube",
        "available": True,
    }

    claims = [
        {
            "text": "The target platform is youtube.",
            "supported": True,
            "source": "supplied_context",
        },
    ]

    result = checker.evaluate(
        facts=facts,
        claims=claims,
    )

    return {
        "version": checker.VERSION,
        "valid": (
            result.get("verdict")
            in FactCheck.VALID_VERDICTS
            and isinstance(
                result.get("checks"),
                dict,
            )
            and isinstance(
                result.get("issues"),
                list,
            )
            and isinstance(
                result.get("warnings"),
                list,
            )
        ),
        "verdict": result.get(
            "verdict"
        ),
        "issues": result.get(
            "issues"
        ),
        "warnings": result.get(
            "warnings"
        ),
    }


if __name__ == "__main__":
    print(
        "=== P9-3 FACTCHECK CORE SELF CHECK ==="
    )

    result = self_check()

    print(
        "VERSION:",
        result["version"],
    )

    print(
        "VERDICT:",
        result["verdict"],
    )

    print(
        "VALID:",
        result["valid"],
    )

    if result["issues"]:
        print(
            "ISSUES:",
            result["issues"],
        )

    if result["warnings"]:
        print(
            "WARNINGS:",
            result["warnings"],
        )

    if result["valid"]:
        print(
            "P9-3 FACTCHECK CORE: PASS"
        )
    else:
        raise SystemExit(
            "P9-3 FACTCHECK CORE: FAIL"
        )
