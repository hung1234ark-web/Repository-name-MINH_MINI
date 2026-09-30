import requests
from urllib.parse import urlparse, parse_qs, unquote


# ==================================================
# MINH MINI - WEB V2.1
# CLEAN SEARCH
# ==================================================

SEARCH_URL = "https://html.duckduckgo.com/html/"


# ==================================================
# GIẢI URL DUCKDUCKGO
# ==================================================

def clean_url(url):
    """Chuyển URL redirect của DuckDuckGo thành URL thật."""

    if not url:
        return ""

    url = url.strip()

    # URL tương đối của DuckDuckGo
    if url.startswith("//duckduckgo.com/l/"):
        url = "https:" + url

    if "duckduckgo.com/l/" in url:

        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            if "uddg" in params:
                real_url = params["uddg"][0]
                return unquote(real_url)

        except Exception:
            pass

    return url


# ==================================================
# KIỂM TRA QUẢNG CÁO
# ==================================================

def is_ad(block):
    """Bỏ kết quả quảng cáo."""

    classes = " ".join(
        block.get("class", [])
    ).lower()

    text = block.get_text(
        " ",
        strip=True
    ).lower()

    ad_words = (
        "ad",
        "advertisement",
        "sponsored"
    )

    for word in ad_words:

        if word in classes:
            return True

    # DuckDuckGo thường đánh dấu quảng cáo trong block
    if "sponsored" in text:
        return True

    if "advertisement" in text:
        return True

    return False


# ==================================================
# TÌM KIẾM WEB
# ==================================================

def search_web(query, max_results=5):

    query = query.strip()

    if not query:
        return []

    try:

        response = requests.get(
            SEARCH_URL,
            params={
                "q": query
            },
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/153.0 Safari/537.36"
                )
            },
            timeout=15
        )

        response.raise_for_status()

        return parse_results(
            response.text,
            max_results
        )

    except requests.exceptions.Timeout:

        return [{
            "title": "Web timeout",
            "text": "Trang tìm kiếm phản hồi quá lâu.",
            "url": ""
        }]

    except requests.exceptions.RequestException as e:

        return [{
            "title": "Web error",
            "text": f"Lỗi kết nối Web: {e}",
            "url": ""
        }]

    except Exception as e:

        return [{
            "title": "Web error",
            "text": f"Lỗi không xác định: {e}",
            "url": ""
        }]


# ==================================================
# PHÂN TÍCH KẾT QUẢ
# ==================================================

def parse_results(html, max_results=5):

    results = []

    try:
        from bs4 import BeautifulSoup

    except ImportError:

        return [{
            "title": "Thiếu thư viện",
            "text": (
                "Hãy cài beautifulsoup4 bằng:\n"
                "py -m pip install beautifulsoup4"
            ),
            "url": ""
        }]

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    result_blocks = soup.select(
        ".result"
    )

    seen_urls = set()

    for block in result_blocks:

        if len(results) >= max_results:
            break

        # ------------------------------
        # Bỏ quảng cáo
        # ------------------------------

        if is_ad(block):
            continue

        # ------------------------------
        # Lấy tiêu đề
        # ------------------------------

        title_tag = block.select_one(
            ".result__title"
        )

        if not title_tag:
            continue

        link_tag = title_tag.find("a")

        if not link_tag:
            continue

        title = link_tag.get_text(
            " ",
            strip=True
        )

        # ------------------------------
        # Lấy URL
        # ------------------------------

        url = link_tag.get(
            "href",
            ""
        ).strip()

        url = clean_url(url)

        if not title or not url:
            continue

        # ------------------------------
        # Bỏ URL trùng
        # ------------------------------

        if url in seen_urls:
            continue

        seen_urls.add(url)

        # ------------------------------
        # Lấy mô tả
        # ------------------------------

        snippet_tag = block.select_one(
            ".result__snippet"
        )

        if snippet_tag:

            text = snippet_tag.get_text(
                " ",
                strip=True
            )

        else:

            text = ""

        # ------------------------------
        # Làm sạch text
        # ------------------------------

        text = " ".join(
            text.split()
        )

        results.append({
            "title": title,
            "text": text,
            "url": url
        })

    return results


# ==================================================
# TÌM KIẾM AN TOÀN
# ==================================================

def safe_search(
    query,
    max_results=5
):

    query = query.strip()

    if len(query) < 2:
        return []

    if len(query) > 300:
        query = query[:300]

    return search_web(
        query,
        max_results=max_results
    )


# ==================================================
# TEST WEB V2.1
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("MINH MINI - WEB V2.1 TEST")
    print("=" * 50)

    query = input(
        "Tìm kiếm: "
    ).strip()

    results = safe_search(
        query
    )

    if not results:

        print(
            "Không tìm thấy kết quả."
        )

    else:

        for i, result in enumerate(
            results,
            1
        ):

            print()
            print(
                f"{i}. {result['title']}"
            )

            if result["text"]:
                print(
                    f"   {result['text']}"
                )

            print(
                f"   {result['url']}"
            )