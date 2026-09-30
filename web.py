# ============================================================
# MINH MINI — WEB FINAL
#
# Luồng:
#
# Lam
#   ↓
# Router Guard
#   ↓
# Brain
#   ↓
# Execution Controller
#   ↓
# WEB
#   ↓
# Search Engine
#   ↓
# Normalize / Filter
#   ↓
# Web Context
#   ↓
# Web AI / Main
#
# Nhiệm vụ:
# - Tìm kiếm web.
# - Chuẩn hóa kết quả.
# - Loại kết quả rỗng / trùng.
# - Giữ URL + tiêu đề + mô tả.
# - Lưu Web Context nếu module có sẵn.
# - Không tự trả lời thay Ollama.
# - Không tự điều khiển Windows.
# ============================================================

from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


# ============================================================
# CONFIG
# ============================================================

DEFAULT_MAX_RESULTS = 10
DEFAULT_TIMEOUT = 15

SEARCH_ENDPOINT = (
    "https://html.duckduckgo.com/html/?q={query}"
)

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/153.0 Safari/537.36 "
    "MINH-MINI"
)


# ============================================================
# OPTIONAL WEB CONTEXT
# ============================================================

try:
    import web_context
except Exception:
    web_context = None


# ============================================================
# RESULT
# ============================================================

@dataclass
class WebResult:
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = "web"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_space(
    value: Any,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip(),
    )


def clean_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    text = html.unescape(
        str(value)
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def clean_url(
    value: Any,
) -> str:
    url = str(
        value or ""
    ).strip()

    url = html.unescape(
        url
    )

    return url.strip()


# ============================================================
# QUERY CLEANUP
# ============================================================

def normalize_query(
    query: Any,
) -> str:

    text = normalize_space(
        query
    )

    if not text:
        return ""

    prefixes = (
        "tìm trên web ",
        "tìm web ",
        "tìm kiếm ",
        "tra cứu ",
        "search ",
        "tìm ",
    )

    lowered = text.lower()

    for prefix in prefixes:

        if lowered.startswith(
            prefix
        ):

            text = text[
                len(prefix):
            ].strip()

            break

    return normalize_space(
        text
    )


# ============================================================
# HTML EXTRACTION
# ============================================================

def remove_html(
    text: str,
) -> str:

    value = html.unescape(
        str(text or "")
    )

    value = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        value,
        flags=re.IGNORECASE
        | re.DOTALL,
    )

    value = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        value,
        flags=re.IGNORECASE
        | re.DOTALL,
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    return clean_text(
        value
    )


def extract_attr(
    tag: str,
    attr: str,
) -> str:

    pattern = (
        rf'{re.escape(attr)}\s*=\s*'
        rf'["\']([^"\']*)["\']'
    )

    match = re.search(
        pattern,
        tag,
        flags=re.IGNORECASE,
    )

    if not match:
        return ""

    return html.unescape(
        match.group(1)
    ).strip()


def extract_href(
    tag: str,
) -> str:

    return extract_attr(
        tag,
        "href",
    )


# ============================================================
# DUCKDUCKGO HTML PARSER
# ============================================================

def parse_search_html(
    page: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[WebResult]:

    results: list[WebResult] = []

    if not page:
        return results

    # DuckDuckGo HTML result blocks.
    blocks = re.findall(
        r'<div[^>]+class="[^"]*result[^"]*"[^>]*>'
        r'.*?'
        r'</div>\s*</div>',
        page,
        flags=re.IGNORECASE
        | re.DOTALL,
    )

    # Fallback: lấy từng result__a nếu block parsing không đủ.
    if not blocks:
        blocks = [
            match
            for match in re.findall(
                r'(<a[^>]+class="[^"]*result__a[^"]*"'
                r'.*?</a>.*?)'
                r'(?=<a[^>]+class="[^"]*result__a|$)',
                page,
                flags=re.IGNORECASE
                | re.DOTALL,
            )
        ]

    seen_urls: set[str] = set()

    for block in blocks:

        if len(results) >= max_results:
            break

        # ----------------------------------------------------
        # TITLE / URL
        # ----------------------------------------------------

        title_match = re.search(
            r'<a[^>]+class="[^"]*result__a[^"]*"'
            r'[^>]*>(.*?)</a>',
            block,
            flags=re.IGNORECASE
            | re.DOTALL,
        )

        if not title_match:
            continue

        raw_title = title_match.group(1)

        title = remove_html(
            raw_title
        )

        href_match = re.search(
            r'<a[^>]+class="[^"]*result__a[^"]*"'
            r'[^>]*href=["\']([^"\']+)["\']',
            block,
            flags=re.IGNORECASE,
        )

        if not href_match:
            continue

        url = clean_url(
            href_match.group(1)
        )

        # DDG có thể trả redirect URL.
        if "uddg=" in url:

            try:
                parsed = urllib.parse.urlparse(
                    url
                )

                params = urllib.parse.parse_qs(
                    parsed.query
                )

                actual = params.get(
                    "uddg"
                )

                if actual:
                    url = (
                        actual[0]
                    )

            except Exception:
                pass

        # ----------------------------------------------------
        # SNIPPET
        # ----------------------------------------------------

        snippet_match = re.search(
            r'<a[^>]+class="[^"]*result__snippet[^"]*"'
            r'[^>]*>(.*?)</a>',
            block,
            flags=re.IGNORECASE
            | re.DOTALL,
        )

        snippet = ""

        if snippet_match:
            snippet = remove_html(
                snippet_match.group(1)
            )

        if not snippet:

            snippet_match = re.search(
                r'<div[^>]+class="[^"]*result__snippet[^"]*"'
                r'[^>]*>(.*?)</div>',
                block,
                flags=re.IGNORECASE
                | re.DOTALL,
            )

            if snippet_match:
                snippet = remove_html(
                    snippet_match.group(1)
                )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        title = clean_text(
            title
        )

        url = clean_url(
            url
        )

        snippet = clean_text(
            snippet
        )

        if not title:
            continue

        if not url:
            continue

        key = url.lower()

        if key in seen_urls:
            continue

        seen_urls.add(
            key
        )

        results.append(
            WebResult(
                title=title,
                url=url,
                snippet=snippet,
                source="duckduckgo",
            )
        )

    return results


# ============================================================
# GENERIC RESULT CLEANUP
# ============================================================

def normalize_results(
    results: Any,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[dict[str, Any]]:

    if results is None:
        return []

    if isinstance(
        results,
        dict,
    ):

        for key in (
            "results",
            "items",
            "sources",
            "data",
        ):

            value = results.get(
                key
            )

            if isinstance(
                value,
                list,
            ):

                results = value
                break

        else:
            results = [
                results
            ]

    if not isinstance(
        results,
        list,
    ):
        results = [
            results
        ]

    normalized: list[
        dict[str, Any]
    ] = []

    seen: set[str] = set()

    for item in results:

        if isinstance(
            item,
            WebResult,
        ):
            data = item.to_dict()

        elif isinstance(
            item,
            dict,
        ):
            data = {
                "title":
                    clean_text(
                        item.get(
                            "title",
                            "",
                        )
                    ),
                "url":
                    clean_url(
                        item.get(
                            "url"
                        )
                        or item.get(
                            "link"
                        )
                        or ""
                    ),
                "snippet":
                    clean_text(
                        item.get(
                            "snippet"
                        )
                        or item.get(
                            "description"
                        )
                        or item.get(
                            "text"
                        )
                        or ""
                    ),
                "source":
                    item.get(
                        "source",
                        "web",
                    ),
            }

        else:
            text = clean_text(
                item
            )

            if not text:
                continue

            data = {
                "title":
                    text,
                "url":
                    "",
                "snippet":
                    text,
                "source":
                    "web",
            }

        title = clean_text(
            data.get(
                "title",
                "",
            )
        )

        url = clean_url(
            data.get(
                "url",
                "",
            )
        )

        snippet = clean_text(
            data.get(
                "snippet",
                "",
            )
        )

        if not title:
            continue

        key = (
            url.lower()
            if url
            else title.lower()
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        normalized.append(
            {
                "title":
                    title,
                "url":
                    url,
                "snippet":
                    snippet,
                "source":
                    data.get(
                        "source",
                        "web",
                    ),
            }
        )

        if len(
            normalized
        ) >= max_results:
            break

    return normalized


# ============================================================
# HTTP SEARCH
# ============================================================

def fetch_search_page(
    query: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:

    encoded = urllib.parse.quote_plus(
        query
    )

    url = SEARCH_ENDPOINT.format(
        query=encoded
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                USER_AGENT,
            "Accept-Language":
                "vi,en-US;q=0.9,en;q=0.8",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:

        raw = response.read()

    return raw.decode(
        "utf-8",
        errors="ignore",
    )


# ============================================================
# WEB SEARCH
# ============================================================

def safe_search(
    query: Any,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> list[dict[str, Any]]:

    normalized_query = normalize_query(
        query
    )

    if not normalized_query:
        return []

    try:

        page = fetch_search_page(
            normalized_query,
            timeout=timeout,
        )

        parsed = parse_search_html(
            page,
            max_results=max_results,
        )

        results = normalize_results(
            parsed,
            max_results=max_results,
        )

    except Exception:
        results = []

    # --------------------------------------------------------
    # LƯU WEB CONTEXT
    # --------------------------------------------------------

    if web_context is not None:

        try:

            store = getattr(
                web_context,
                "store_results",
                None,
            )

            if callable(store):
                store(
                    normalized_query,
                    results,
                )

        except Exception:
            # Web search không được chết chỉ vì
            # Web Context lỗi.
            pass

    return results


# ============================================================
# ALIASES
# ============================================================

def search(
    query: Any,
    max_results: int = DEFAULT_MAX_RESULTS,
    **kwargs: Any,
) -> list[dict[str, Any]]:

    return safe_search(
        query,
        max_results=max_results,
        **kwargs,
    )


def search_web(
    query: Any,
    max_results: int = DEFAULT_MAX_RESULTS,
    **kwargs: Any,
) -> list[dict[str, Any]]:

    return safe_search(
        query,
        max_results=max_results,
        **kwargs,
    )


def web_search(
    query: Any,
    max_results: int = DEFAULT_MAX_RESULTS,
    **kwargs: Any,
) -> list[dict[str, Any]]:

    return safe_search(
        query,
        max_results=max_results,
        **kwargs,
    )


# ============================================================
# RESULT FORMAT
# ============================================================

def format_results(
    results: Any,
    limit: int = DEFAULT_MAX_RESULTS,
) -> str:

    items = normalize_results(
        results,
        max_results=limit,
    )

    if not items:
        return ""

    lines: list[str] = []

    for index, item in enumerate(
        items,
        start=1,
    ):

        title = item.get(
            "title",
            f"Nguồn {index}",
        )

        snippet = item.get(
            "snippet",
            "",
        )

        url = item.get(
            "url",
            "",
        )

        block = (
            f"{index}. {title}"
        )

        if snippet:
            block += (
                f"\n   {snippet}"
            )

        if url:
            block += (
                f"\n   {url}"
            )

        lines.append(
            block
        )

    return "\n".join(
        lines
    )


def summarize_metadata(
    results: Any,
) -> dict[str, Any]:

    items = normalize_results(
        results
    )

    domains: list[str] = []

    for item in items:

        url = item.get(
            "url",
            "",
        )

        if not url:
            continue

        try:

            parsed = urllib.parse.urlparse(
                url
            )

            domain = (
                parsed.netloc
                .lower()
                .removeprefix(
                    "www."
                )
            )

            if (
                domain
                and domain not in domains
            ):
                domains.append(
                    domain
                )

        except Exception:
            continue

    return {
        "count":
            len(items),
        "domains":
            domains,
    }


# ============================================================
# CONTEXT HELPERS
# ============================================================

def get_current_context() -> dict[str, Any]:

    if web_context is None:
        return {}

    try:

        fn = getattr(
            web_context,
            "current_context",
            None,
        )

        if callable(fn):

            result = fn()

            if isinstance(
                result,
                dict,
            ):
                return result

    except Exception:
        pass

    return {}


def get_current_sources() -> list[dict[str, Any]]:

    if web_context is None:
        return []

    try:

        fn = getattr(
            web_context,
            "get_all_sources",
            None,
        )

        if callable(fn):

            result = fn()

            if isinstance(
                result,
                list,
            ):
                return result

    except Exception:
        pass

    return []


# ============================================================
# INFO
# ============================================================

def describe() -> dict[str, Any]:

    return {
        "module":
            "MINH MINI — WEB FINAL",

        "search_engine":
            "DuckDuckGo HTML",

        "safe_search":
            True,

        "stores_web_context":
            web_context is not None,

        "default_max_results":
            DEFAULT_MAX_RESULTS,

        "public_functions": [
            "safe_search",
            "search",
            "search_web",
            "web_search",
            "normalize_query",
            "normalize_results",
            "format_results",
            "summarize_metadata",
            "get_current_context",
            "get_current_sources",
        ],
    }


# ============================================================
# SELF CHECK
# ============================================================

def _self_check() -> bool:

    # Không gọi internet.
    # Chỉ kiểm tra logic local.

    assert (
        normalize_query(
            "tìm trên web giá iphone"
        )
        == "giá iphone"
    )

    assert (
        normalize_query(
            "search sony zve10"
        )
        == "sony zve10"
    )

    raw = [
        {
            "title":
                "Nguồn A",
            "url":
                "https://example.com/a",
            "snippet":
                "Thông tin A",
        },
        {
            "title":
                "Nguồn A",
            "url":
                "https://example.com/a",
            "snippet":
                "Trùng",
        },
        {
            "title":
                "Nguồn B",
            "url":
                "https://example.com/b",
            "snippet":
                "Thông tin B",
        },
    ]

    normalized = normalize_results(
        raw
    )

    assert len(
        normalized
    ) == 2

    assert (
        normalized[0]["title"]
        == "Nguồn A"
    )

    formatted = format_results(
        normalized
    )

    assert "Nguồn A" in formatted
    assert "Nguồn B" in formatted

    metadata = summarize_metadata(
        normalized
    )

    assert metadata["count"] == 2
    assert (
        "example.com"
        in metadata["domains"]
    )

    # Query rỗng phải an toàn.
    assert safe_search("") == []

    return True


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    try:

        _self_check()

        print(
            "WEB FINAL: READY"
        )

    except Exception as exc:

        print(
            "WEB FINAL: "
            f"ERROR: {exc}"
        )