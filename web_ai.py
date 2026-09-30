# ============================================================
# MINH MINI — WEB AI FINAL
#
# Nhiệm vụ:
# WEB RESULTS
#      ↓
# NORMALIZE
#      ↓
# BUILD EVIDENCE
#      ↓
# OLLAMA
#      ↓
# AI SUMMARY
#
# NGUYÊN TẮC:
# - Không tự tìm web.
# - Không tự thực hiện Windows action.
# - Không bịa nguồn.
# - Chỉ tổng hợp từ kết quả web được truyền vào.
# - Nếu không đủ dữ liệu -> nói rõ không đủ dữ liệu.
# - Giữ URL để Minh có thể truy ngược nguồn.
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path.home() / "MINH_MINI"
CONFIG_FILE = BASE_DIR / "config" / "config.json"


# ============================================================
# RESULT
# ============================================================

@dataclass
class WebAISource:
    number: int
    title: str = ""
    url: str = ""
    snippet: str = ""


@dataclass
class WebAIResult:
    query: str
    answer: str
    sources: list[WebAISource]
    success: bool = True
    error: str = ""


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def load_config() -> dict:
    try:
        if not CONFIG_FILE.exists():
            return {}

        data = json.loads(
            CONFIG_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def get_ollama_config() -> tuple[str, str]:
    config = load_config()

    ollama = config.get(
        "ollama",
        {},
    )

    if not isinstance(ollama, dict):
        ollama = {}

    url = (
        ollama.get("url")
        or config.get("ollama_url")
        or config.get("url")
        or "http://localhost:11434"
    )

    model = (
        ollama.get("model")
        or config.get("model")
        or "qwen3:1.7b"
    )

    return (
        clean_text(url),
        clean_text(model),
    )


# ============================================================
# SOURCE NORMALIZATION
# ============================================================

def normalize_source(
    item: Any,
    number: int,
) -> WebAISource:

    if isinstance(
        item,
        WebAISource,
    ):
        return item

    if isinstance(
        item,
        dict,
    ):
        title = clean_text(
            item.get("title")
        )

        url = clean_text(
            item.get("url")
            or item.get("link")
        )

        snippet = clean_text(
            item.get("snippet")
            or item.get("description")
            or item.get("text")
        )

        return WebAISource(
            number=number,
            title=title,
            url=url,
            snippet=snippet,
        )

    return WebAISource(
        number=number,
        title=clean_text(item),
    )


def normalize_sources(
    results: Any,
    max_sources: int = 8,
) -> list[WebAISource]:

    if not isinstance(
        results,
        (list, tuple),
    ):
        return []

    sources = []

    for index, item in enumerate(
        results[:max_sources],
        start=1,
    ):
        source = normalize_source(
            item,
            index,
        )

        if (
            not source.title
            and not source.snippet
            and not source.url
        ):
            continue

        sources.append(source)

    return sources


# ============================================================
# EVIDENCE
# ============================================================

def build_evidence(
    query: str,
    sources: list[WebAISource],
) -> str:

    lines = [
        f"QUERY: {query}",
        "",
        "SOURCES:",
    ]

    for source in sources:
        lines.append(
            f"[Nguồn {source.number}]"
        )

        if source.title:
            lines.append(
                f"Tiêu đề: {source.title}"
            )

        if source.snippet:
            lines.append(
                f"Nội dung: {source.snippet}"
            )

        if source.url:
            lines.append(
                f"URL: {source.url}"
            )

        lines.append("")

    return "\n".join(lines).strip()


# ============================================================
# OLLAMA
# ============================================================

def call_ollama(
    prompt: str,
) -> str:

    try:
        import requests
    except Exception:
        return ""

    url, model = get_ollama_config()

    endpoint = url.rstrip("/")

    if not endpoint.endswith(
        "/api/chat"
    ):
        endpoint += "/api/chat"

    system_prompt = """
Bạn là Web AI của Minh Mini.

NHIỆM VỤ:
Tóm tắt và phân tích thông tin từ các nguồn
web được cung cấp.

QUY TẮC BẮT BUỘC:

1. Chỉ sử dụng thông tin xuất hiện trong dữ liệu
   nguồn được cung cấp.

2. Không tự bịa:
   - giá
   - ngày tháng
   - số liệu
   - tên sản phẩm
   - nguồn
   - URL
   - kết luận không có bằng chứng.

3. Nếu các nguồn mâu thuẫn:
   nói rõ rằng nguồn đang có thông tin khác nhau.

4. Nếu dữ liệu không đủ:
   nói rõ chưa đủ dữ liệu.

5. Không được tạo URL mới.

6. Không được nói rằng Minh đã thực hiện một
   hành động Windows.

7. Trả lời bằng tiếng Việt.

8. Ưu tiên:
   - ngắn gọn
   - rõ ràng
   - đúng dữ liệu
   - dễ hiểu.

9. Khi có thể, hãy nhắc:
   "Theo nguồn 1..."
   "Nguồn 2 cho biết..."

10. Không thêm danh sách nguồn giả.
"""

    try:
        response = requests.post(
            endpoint,
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        answer = (
            data.get("message", {})
            .get("content", "")
        )

        return clean_text(answer)

    except Exception:
        return ""


# ============================================================
# FALLBACK
# ============================================================

def fallback_summary(
    query: str,
    sources: list[WebAISource],
) -> str:

    if not sources:
        return (
            "Minh chưa có đủ dữ liệu web để trả lời "
            "câu này."
        )

    lines = [
        f"Minh tìm được thông tin liên quan đến: {query}",
        "",
    ]

    for source in sources[:5]:

        if source.title:
            lines.append(
                f"- Nguồn {source.number}: "
                f"{source.title}"
            )

        if source.snippet:
            lines.append(
                f"  {source.snippet}"
            )

    lines.append("")
    lines.append(
        "Minh chưa thể tổng hợp sâu hơn vì Web AI "
        "chưa trả về câu trả lời."
    )

    return "\n".join(lines)


# ============================================================
# MAIN SUMMARIZER
# ============================================================

def summarize_results(
    query: str = "",
    results: Any = None,
    **kwargs,
) -> str:

    query = clean_text(query)

    if not query:
        return (
            "Minh chưa nhận được nội dung cần tìm."
        )

    sources = normalize_sources(
        results
    )

    if not sources:
        return (
            "Minh không có nguồn web đủ dữ liệu "
            "để tổng hợp."
        )

    evidence = build_evidence(
        query,
        sources,
    )

    prompt = f"""
Hãy trả lời yêu cầu của Lam dựa CHỈ trên
dữ liệu nguồn bên dưới.

Yêu cầu:
{query}

Dữ liệu nguồn:
{evidence}

Hãy:
- trả lời trực tiếp vấn đề;
- chỉ dùng thông tin có trong nguồn;
- nếu chưa đủ dữ liệu thì nói rõ;
- nếu nguồn mâu thuẫn thì nêu rõ;
- không bịa thêm.
"""

    answer = call_ollama(
        prompt
    )

    if answer:
        return answer

    return fallback_summary(
        query,
        sources,
    )


# ============================================================
# STRUCTURED RESULT
# ============================================================

def summarize_structured(
    query: str = "",
    results: Any = None,
    **kwargs,
) -> WebAIResult:

    query = clean_text(query)

    sources = normalize_sources(
        results
    )

    if not sources:
        return WebAIResult(
            query=query,
            answer=(
                "Minh không có đủ nguồn để "
                "tổng hợp thông tin."
            ),
            sources=[],
            success=False,
            error="NO_SOURCES",
        )

    answer = summarize_results(
        query=query,
        results=results,
    )

    return WebAIResult(
        query=query,
        answer=answer,
        sources=sources,
        success=bool(answer),
    )


# ============================================================
# SOURCE FORMAT
# ============================================================

def format_sources(
    results: Any,
    max_sources: int = 8,
) -> str:

    sources = normalize_sources(
        results,
        max_sources=max_sources,
    )

    if not sources:
        return "Chưa có nguồn."

    lines = []

    for source in sources:
        lines.append(
            f"{source.number}. "
            f"{source.title or 'Không có tiêu đề'}"
        )

        if source.url:
            lines.append(
                f"   {source.url}"
            )

    return "\n".join(lines)


# ============================================================
# PUBLIC ALIASES
# ============================================================

summarize = summarize_results
summarize_web = summarize_results
web_ai = summarize_results


# ============================================================
# DESCRIPTION
# ============================================================

def describe() -> dict:
    url, model = get_ollama_config()

    return {
        "module": "web_ai",
        "status": "ready",
        "ollama_url": url,
        "model": model,
        "source_grounded": True,
        "can_search_web": False,
        "can_control_windows": False,
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> bool:

    required = (
        "summarize_results",
        "summarize_structured",
        "normalize_sources",
        "build_evidence",
        "call_ollama",
    )

    missing = [
        name
        for name in required
        if name not in globals()
    ]

    if missing:
        print(
            "WEB AI SELF CHECK FAIL:",
            ", ".join(missing),
        )
        return False

    print(
        "WEB AI SELF CHECK PASS"
    )

    return True


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    _self_check()