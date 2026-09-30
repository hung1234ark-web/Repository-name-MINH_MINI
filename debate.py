# ============================================================
# MINH MINI — DEBATE LAYER
# VERSION: DEBATE-1.1
#
# PURPOSE
#   Technical decision-support layer.
#
# CORE PRINCIPLE
#   /debate analyzes before implementation.
#
# IMPORTANT
#   - Does NOT edit files.
#   - Does NOT execute commands.
#   - Does NOT install software.
#   - Does NOT change architecture.
#   - Does NOT automatically add/remove/replace AI.
#   - Final decision belongs to LAM.
#
# OUTPUT
#   A/B comparison
#   -> impact
#   -> risks
#   -> feasibility
#   -> recommendation
#   -> LAM decision
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import re


VERSION = "DEBATE-1.1"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class DebateOption:
    """
    One technical option in a debate.
    """

    name: str
    benefits: List[str] = field(default_factory=list)
    drawbacks: List[str] = field(default_factory=list)
    impact: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    feasibility: str = "UNKNOWN"
    feasibility_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "benefits": list(self.benefits),
            "drawbacks": list(self.drawbacks),
            "impact": list(self.impact),
            "risks": list(self.risks),
            "feasibility": self.feasibility,
            "feasibility_reason": self.feasibility_reason,
        }


@dataclass
class DebateResult:
    question: str
    topic: str
    question_type: str

    summary: str

    options: List[DebateOption] = field(default_factory=list)

    benefits: List[str] = field(default_factory=list)
    drawbacks: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    impacts: List[str] = field(default_factory=list)

    missing_information: List[str] = field(default_factory=list)

    recommended_option: str = ""
    recommendation_reason: str = ""

    requires_lam_decision: bool = True
    executable: bool = False

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "topic": self.topic,
            "question_type": self.question_type,
            "summary": self.summary,
            "options": [
                option.to_dict()
                for option in self.options
            ],
            "benefits": list(self.benefits),
            "drawbacks": list(self.drawbacks),
            "risks": list(self.risks),
            "impacts": list(self.impacts),
            "missing_information": list(
                self.missing_information
            ),
            "recommended_option": self.recommended_option,
            "recommendation_reason": self.recommendation_reason,
            "requires_lam_decision": self.requires_lam_decision,
            "executable": self.executable,
            "created_at": self.created_at,
        }


# ============================================================
# DEBATE ENGINE
# ============================================================

class DebateEngine:
    """
    Technical debate / decision-support engine.

    /debate is deliberately separated from execution.

    It can:
        - classify the question
        - identify options
        - compare trade-offs
        - identify risks
        - assess feasibility
        - produce a technical recommendation

    It cannot:
        - modify project files
        - execute code
        - install packages
        - alter architecture
        - perform the decision automatically
    """

    COMMAND = "/debate"

    def __init__(self) -> None:
        self.last_result: Optional[DebateResult] = None
        self.history: List[DebateResult] = []

    # ========================================================
    # COMMAND
    # ========================================================

    @classmethod
    def is_debate_command(cls, text: Any) -> bool:
        if not isinstance(text, str):
            return False

        value = text.strip().lower()

        if not value:
            return False

        return (
            value == cls.COMMAND
            or value.startswith(cls.COMMAND + " ")
            or value.startswith(cls.COMMAND + "\n")
            or value.startswith(cls.COMMAND + "\t")
        )

    @classmethod
    def extract_question(cls, text: Any) -> str:
        if not isinstance(text, str):
            return ""

        value = text.strip()

        if not cls.is_debate_command(value):
            return value

        return value[len(cls.COMMAND):].strip()

    # ========================================================
    # QUESTION CLASSIFICATION
    # ========================================================

    @staticmethod
    def detect_topic(question: str) -> str:
        value = question.lower()

        if any(
            key in value
            for key in (
                "ai",
                "model",
                "llm",
                "ollama",
                "qwen",
                "gemma",
                "llama",
                "gpt",
                "agent",
                "mô hình",
            )
        ):
            return "AI / MODEL"

        if any(
            key in value
            for key in (
                "code",
                "python",
                "file",
                "module",
                "function",
                "class",
                "bug",
                "lỗi",
                "sửa",
                "script",
            )
        ):
            return "CODE"

        if any(
            key in value
            for key in (
                "kiến trúc",
                "architecture",
                "router",
                "executor",
                "memory",
                "brain",
                "orchestrator",
                "pipeline",
            )
        ):
            return "ARCHITECTURE"

        if any(
            key in value
            for key in (
                "web",
                "search",
                "agent reach",
                "internet",
                "github",
                "browser",
                "tool",
            )
        ):
            return "WEB / TOOL"

        if any(
            key in value
            for key in (
                "thêm",
                "xóa",
                "thay",
                "tích hợp",
                "integrate",
                "integration",
                "chức năng",
                "feature",
                "đổi",
            )
        ):
            return "PROJECT CHANGE"

        return "GENERAL TECHNICAL"

    @staticmethod
    def detect_question_type(question: str) -> str:
        value = question.lower()

        if any(
            phrase in value
            for phrase in (
                "có nên",
                "nên thêm",
                "nên thay",
                "nên xóa",
                "có cần",
                "nên dùng",
                "chọn a hay b",
                "chọn",
                "should we",
                "should i",
                "which",
                "worth",
            )
        ):
            return "DECISION"

        if any(
            phrase in value
            for phrase in (
                "so sánh",
                "hay",
                "vs",
                "versus",
                "compare",
                "khác nhau",
            )
        ):
            return "COMPARISON"

        if any(
            phrase in value
            for phrase in (
                "tại sao",
                "vì sao",
                "why",
            )
        ):
            return "EXPLANATION"

        return "TECHNICAL_ANALYSIS"

    # ========================================================
    # MISSING INFORMATION
    # ========================================================

    @staticmethod
    def find_missing_information(
        question: str,
    ) -> List[str]:

        missing: List[str] = []

        value = question.strip()
        lower = value.lower()

        if not value:
            missing.append(
                "Câu hỏi cụ thể cần được cung cấp."
            )

        if re.search(
            r"\b(này|đó|nó|ai này|con này|model này)\b",
            lower,
        ):
            missing.append(
                "Tên hoặc thông tin cụ thể của "
                "AI/model/thành phần đang được nhắc tới."
            )

        if (
            any(
                word in lower
                for word in (
                    "thêm",
                    "tích hợp",
                    "integrate",
                )
            )
            and len(value.split()) < 6
        ):
            missing.append(
                "Mục tiêu và chức năng mà thành phần mới "
                "cần đảm nhiệm."
            )

        return missing

    # ========================================================
    # OPTION DETECTION
    # ========================================================

    @staticmethod
    def detect_explicit_options(
        question: str,
    ) -> List[str]:

        value = question.strip()

        options: List[str] = []

        # A vs B
        match = re.search(
            r"\bA\b\s+(?:vs|VS|hay|hoặc)\s+\bB\b",
            value,
            re.IGNORECASE,
        )

        if match:
            return ["A", "B"]

        # "A hay B"
        match = re.search(
            r"\b(.{1,80}?)\s+hay\s+(.{1,80}?)(?:\?|$)",
            value,
            re.IGNORECASE,
        )

        if match:
            first = match.group(1).strip()
            second = match.group(2).strip()

            if first and second:
                options.extend(
                    [
                        first,
                        second,
                    ]
                )

        return options

    # ========================================================
    # GENERIC OPTIONS
    # ========================================================

    @staticmethod
    def build_default_options(
        topic: str,
    ) -> List[DebateOption]:

        if topic == "AI / MODEL":
            return [
                DebateOption(
                    name="A — Giữ hệ thống/model hiện tại",
                    benefits=[
                        "Không tăng độ phức tạp.",
                        "Giảm thay đổi đối với hệ thống đang ổn định.",
                        "Dễ kiểm thử và rollback.",
                    ],
                    drawbacks=[
                        "Có thể bỏ lỡ năng lực mới.",
                    ],
                    impact=[
                        "Tác động kiến trúc thấp.",
                        "Ít ảnh hưởng routing và context.",
                    ],
                    risks=[
                        "Có thể thiếu năng lực nếu yêu cầu mới vượt khả năng hiện tại.",
                    ],
                    feasibility="CAO",
                    feasibility_reason=(
                        "Không cần thay đổi lớn trong hệ thống."
                    ),
                ),
                DebateOption(
                    name="B — Thêm/thay bằng AI/model mới",
                    benefits=[
                        "Có thể bổ sung năng lực mới.",
                        "Có thể cải thiện một số nhiệm vụ chuyên biệt.",
                    ],
                    drawbacks=[
                        "Tăng độ phức tạp.",
                        "Có thể cần routing hoặc quản lý model."
                    ],
                    impact=[
                        "Có thể ảnh hưởng kiến trúc xử lý.",
                        "Có thể tăng nhu cầu tài nguyên."
                    ],
                    risks=[
                        "Chồng chéo trách nhiệm.",
                        "Regression nếu tích hợp không đúng.",
                    ],
                    feasibility="TRUNG BÌNH",
                    feasibility_reason=(
                        "Cần kiểm tra khả năng tích hợp và tài nguyên."
                    ),
                ),
            ]

        if topic == "ARCHITECTURE":
            return [
                DebateOption(
                    name="A — Giữ kiến trúc hiện tại",
                    benefits=[
                        "Ổn định.",
                        "Ít regression.",
                        "Dễ kiểm thử."
                    ],
                    drawbacks=[
                        "Có thể giới hạn khả năng mở rộng."
                    ],
                    impact=[
                        "Tác động thấp."
                    ],
                    risks=[
                        "Có thể phải xử lý workaround nếu kiến trúc hiện tại thiếu khả năng cần thiết."
                    ],
                    feasibility="CAO",
                    feasibility_reason=(
                        "Không thay đổi các thành phần lõi."
                    ),
                ),
                DebateOption(
                    name="B — Thay đổi kiến trúc",
                    benefits=[
                        "Có thể giải quyết hạn chế cấu trúc hiện tại.",
                        "Có thể tạo nền tảng mở rộng tốt hơn."
                    ],
                    drawbacks=[
                        "Phạm vi thay đổi lớn.",
                        "Cần kiểm thử rộng hơn."
                    ],
                    impact=[
                        "Ảnh hưởng nhiều module."
                    ],
                    risks=[
                        "Regression.",
                        "Tăng độ phức tạp.",
                        "Khó rollback nếu thay đổi quá rộng."
                    ],
                    feasibility="TRUNG BÌNH",
                    feasibility_reason=(
                        "Cần xác định rõ phạm vi và dependency trước khi thực hiện."
                    ),
                ),
            ]

        return [
            DebateOption(
                name="A — Giữ nguyên",
                benefits=[
                    "Ít thay đổi.",
                    "Giảm rủi ro."
                ],
                drawbacks=[
                    "Có thể không đạt được mục tiêu mới."
                ],
                impact=[
                    "Tác động thấp."
                ],
                risks=[
                    "Có thể thiếu chức năng cần thiết."
                ],
                feasibility="CAO",
                feasibility_reason=(
                    "Không yêu cầu thay đổi hệ thống."
                ),
            ),
            DebateOption(
                name="B — Thay đổi / bổ sung",
                benefits=[
                    "Có thể đáp ứng mục tiêu mới."
                ],
                drawbacks=[
                    "Tăng phạm vi công việc."
                ],
                impact=[
                    "Có tác động đến hệ thống hiện tại."
                ],
                risks=[
                    "Có thể phát sinh lỗi hoặc dependency mới."
                ],
                feasibility="TRUNG BÌNH",
                feasibility_reason=(
                    "Cần kiểm tra chi tiết trước khi thực hiện."
                ),
            ),
        ]

    # ========================================================
    # RECOMMENDATION
    # ========================================================

    @staticmethod
    def choose_recommendation(
        options: List[DebateOption],
        missing_information: List[str],
    ) -> tuple[str, str]:

        if missing_information:
            return (
                "CHƯA ĐỦ DỮ LIỆU",
                (
                    "Không nên đưa ra lựa chọn cuối cùng khi còn "
                    "thiếu thông tin có thể ảnh hưởng trực tiếp "
                    "đến quyết định."
                ),
            )

        if not options:
            return (
                "CHƯA XÁC ĐỊNH",
                "Chưa xác định được các phương án để so sánh.",
            )

        # Prefer the option with the strongest feasibility.
        priority = {
            "CAO": 3,
            "TRUNG BÌNH": 2,
            "THẤP": 1,
            "UNKNOWN": 0,
        }

        ranked = sorted(
            options,
            key=lambda option: priority.get(
                option.feasibility,
                0,
            ),
            reverse=True,
        )

        top = ranked[0]

        if len(ranked) > 1:
            second = ranked[1]

            if (
                priority.get(top.feasibility, 0)
                == priority.get(second.feasibility, 0)
            ):
                return (
                    "CHƯA CÓ ƯU THẾ RÕ RÀNG",
                    (
                        "Các phương án có mức khả thi tương đương. "
                        "Cần so sánh mục tiêu cụ thể trước khi chọn."
                    ),
                )

        return (
            top.name,
            (
                f"Minh khuyến nghị ưu tiên {top.name} vì mức khả thi "
                f"được đánh giá là {top.feasibility}. "
                f"{top.feasibility_reason}"
            ),
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DebateResult:

        question = self.extract_question(
            question or ""
        ).strip()

        context = context or {}

        topic = self.detect_topic(question)
        question_type = self.detect_question_type(question)

        missing = self.find_missing_information(
            question
        )

        explicit_options = self.detect_explicit_options(
            question
        )

        if explicit_options:
            options = [
                DebateOption(
                    name=name,
                    benefits=[
                        "Cần đánh giá theo mục tiêu thực tế của MINH MINI."
                    ],
                    drawbacks=[
                        "Chưa có đủ dữ liệu cụ thể để kết luận ưu/nhược điểm."
                    ],
                    impact=[
                        "Cần kiểm tra ảnh hưởng đến kiến trúc hiện tại."
                    ],
                    risks=[
                        "Không nên tích hợp trước khi kiểm tra compatibility."
                    ],
                    feasibility="UNKNOWN",
                    feasibility_reason=(
                        "Cần thông tin cụ thể về phương án."
                    ),
                )
                for name in explicit_options
            ]
        else:
            options = self.build_default_options(
                topic
            )

        benefits: List[str] = []
        drawbacks: List[str] = []
        risks: List[str] = []
        impacts: List[str] = []

        for option in options:
            benefits.extend(
                option.benefits
            )
            drawbacks.extend(
                option.drawbacks
            )
            risks.extend(
                option.risks
            )
            impacts.extend(
                option.impact
            )

        # Remove duplicates while preserving order.
        benefits = list(dict.fromkeys(benefits))
        drawbacks = list(dict.fromkeys(drawbacks))
        risks = list(dict.fromkeys(risks))
        impacts = list(dict.fromkeys(impacts))

        recommended_option, recommendation_reason = (
            self.choose_recommendation(
                options,
                missing,
            )
        )

        summary = (
            f"Đây là yêu cầu {question_type.lower()} "
            f"thuộc nhóm {topic}. "
            "DEBATE phân tích trước khi thực hiện và "
            "không tự thay đổi hệ thống."
        )

        active_files = context.get(
            "active_files"
        )

        if active_files:
            impacts.append(
                f"Có thể đối chiếu với {len(active_files)} "
                "file active được cung cấp trong context."
            )

        result = DebateResult(
            question=question,
            topic=topic,
            question_type=question_type,
            summary=summary,
            options=options,
            benefits=benefits,
            drawbacks=drawbacks,
            risks=risks,
            impacts=impacts,
            missing_information=missing,
            recommended_option=recommended_option,
            recommendation_reason=recommendation_reason,
            requires_lam_decision=True,
            executable=False,
        )

        self.last_result = result
        self.history.append(result)

        return result

    # ========================================================
    # FORMAT
    # ========================================================

    @staticmethod
    def format_result(
        result: DebateResult,
    ) -> str:

        lines: List[str] = []

        lines.append(
            "=== MINH MINI /DEBATE ==="
        )
        lines.append("")

        lines.append(
            f"CÂU HỎI: {result.question}"
        )
        lines.append(
            f"CHỦ ĐỀ: {result.topic}"
        )
        lines.append(
            f"LOẠI: {result.question_type}"
        )
        lines.append("")

        lines.append(
            "PHÂN TÍCH"
        )
        lines.append(
            result.summary
        )
        lines.append("")

        # ----------------------------------------------------
        # OPTIONS
        # ----------------------------------------------------

        if result.options:
            lines.append(
                "CÁC PHƯƠNG ÁN"
            )

            for index, option in enumerate(
                result.options,
                start=1,
            ):
                lines.append(
                    f"{index}. {option.name}"
                )

                lines.append(
                    f"   Khả thi: {option.feasibility}"
                )

                if option.feasibility_reason:
                    lines.append(
                        f"   Vì sao: {option.feasibility_reason}"
                    )

                if option.benefits:
                    lines.append(
                        "   Ưu điểm:"
                    )
                    for item in option.benefits:
                        lines.append(
                            f"   + {item}"
                        )

                if option.drawbacks:
                    lines.append(
                        "   Nhược điểm:"
                    )
                    for item in option.drawbacks:
                        lines.append(
                            f"   - {item}"
                        )

                if option.impact:
                    lines.append(
                        "   Tác động:"
                    )
                    for item in option.impact:
                        lines.append(
                            f"   → {item}"
                        )

                if option.risks:
                    lines.append(
                        "   Rủi ro:"
                    )
                    for item in option.risks:
                        lines.append(
                            f"   ⚠ {item}"
                        )

                lines.append("")

        # ----------------------------------------------------
        # OVERALL IMPACT
        # ----------------------------------------------------

        if result.impacts:
            lines.append(
                "TÁC ĐỘNG ĐẾN MINH MINI"
            )

            for item in result.impacts:
                lines.append(
                    f"- {item}"
                )

            lines.append("")

        # ----------------------------------------------------
        # RISKS
        # ----------------------------------------------------

        if result.risks:
            lines.append(
                "RỦI RO CẦN TRÁNH"
            )

            for item in result.risks:
                lines.append(
                    f"⚠ {item}"
                )

            lines.append("")

        # ----------------------------------------------------
        # MISSING INFORMATION
        # ----------------------------------------------------

        if result.missing_information:
            lines.append(
                "THÔNG TIN CÒN THIẾU"
            )

            for item in result.missing_information:
                lines.append(
                    f"- {item}"
                )

            lines.append("")

        # ----------------------------------------------------
        # RECOMMENDATION
        # ----------------------------------------------------

        lines.append(
            "KHUYẾN NGHỊ KỸ THUẬT"
        )
        lines.append(
            f"→ {result.recommended_option}"
        )
        lines.append(
            f"Lý do: {result.recommendation_reason}"
        )
        lines.append("")

        # ----------------------------------------------------
        # DECISION
        # ----------------------------------------------------

        lines.append(
            "QUYỀN QUYẾT ĐỊNH"
        )
        lines.append(
            "→ LAM"
        )
        lines.append(
            "Lam có thể chọn phương án được khuyến nghị, "
            "chọn phương án khác, hoặc yêu cầu phân tích thêm."
        )
        lines.append("")

        # ----------------------------------------------------
        # EXECUTION SAFETY
        # ----------------------------------------------------

        lines.append(
            "THỰC THI"
        )
        lines.append(
            "→ KHÔNG TỰ ĐỘNG THỰC HIỆN"
        )

        return "\n".join(lines)

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> Dict[str, Any]:

        return {
            "module": "debate",
            "version": VERSION,
            "command": self.COMMAND,
            "history_count": len(self.history),
            "has_last_result": (
                self.last_result is not None
            ),

            # Safety
            "analysis_enabled": True,
            "recommendation_enabled": True,
            "execution_enabled": False,
            "file_write_enabled": False,
            "package_install_enabled": False,
            "architecture_change_enabled": False,
            "automatic_ai_change_enabled": False,

            # Human decision
            "lam_decision_required": True,
        }

    # ========================================================
    # SELF CHECK
    # ========================================================

    def self_check(self) -> Dict[str, Any]:

        results: Dict[str, Any] = {
            "module": "debate",
            "version": VERSION,

            "command_detection": False,
            "question_extraction": False,
            "topic_detection": False,
            "option_analysis": False,
            "recommendation": False,
            "execution_blocked": False,
            "lam_decision_required": False,

            "passed": False,
        }

        try:
            command = (
                "/debate Có nên thêm một AI mới "
                "vào MINH MINI không?"
            )

            results["command_detection"] = (
                self.is_debate_command(command)
            )

            question = self.extract_question(
                command
            )

            results["question_extraction"] = (
                bool(question)
                and not question.startswith(
                    self.COMMAND
                )
                and question != command
            )

            results["topic_detection"] = (
                self.detect_topic(question)
                == "AI / MODEL"
            )

            result = self.analyze(
                question
            )

            results["option_analysis"] = (
                isinstance(
                    result,
                    DebateResult,
                )
                and len(result.options) >= 2
            )

            results["recommendation"] = (
                bool(
                    result.recommended_option
                )
                and bool(
                    result.recommendation_reason
                )
            )

            results["execution_blocked"] = (
                result.executable is False
                and self.status()[
                    "execution_enabled"
                ] is False
                and self.status()[
                    "file_write_enabled"
                ] is False
                and self.status()[
                    "automatic_ai_change_enabled"
                ] is False
            )

            results["lam_decision_required"] = (
                result.requires_lam_decision is True
                and self.status()[
                    "lam_decision_required"
                ] is True
            )

            test_keys = (
                "command_detection",
                "question_extraction",
                "topic_detection",
                "option_analysis",
                "recommendation",
                "execution_blocked",
                "lam_decision_required",
            )

            results["passed"] = all(
                results[key] is True
                for key in test_keys
            )

        except Exception as exc:
            results["error"] = repr(exc)
            results["passed"] = False

        return results


# ============================================================
# SINGLETON
# ============================================================

_DEBATE: Optional[DebateEngine] = None


def get_debate() -> DebateEngine:
    global _DEBATE

    if _DEBATE is None:
        _DEBATE = DebateEngine()

    return _DEBATE


# ============================================================
# PUBLIC API
# ============================================================

def is_debate_command(
    text: Any,
) -> bool:
    return get_debate().is_debate_command(
        text
    )


def extract_question(
    text: Any,
) -> str:
    return get_debate().extract_question(
        text
    )


def analyze(
    question: str,
    context: Optional[Dict[str, Any]] = None,
) -> DebateResult:

    return get_debate().analyze(
        question,
        context=context,
    )


def debate(
    question: str,
    context: Optional[Dict[str, Any]] = None,
) -> str:

    result = analyze(
        question,
        context=context,
    )

    return get_debate().format_result(
        result
    )


def status() -> Dict[str, Any]:
    return get_debate().status()


def self_check() -> Dict[str, Any]:
    return get_debate().self_check()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":
    import json

    engine = get_debate()

    print(
        json.dumps(
            engine.self_check(),
            ensure_ascii=False,
            indent=2,
        )
    )

    print()

    test_question = (
        "/debate Có nên thêm một AI mới "
        "vào MINH MINI không?"
    )

    result = engine.analyze(
        test_question
    )

    print(
        engine.format_result(
            result
        )
    )