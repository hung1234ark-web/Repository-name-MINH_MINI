import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote


SEARCH_URL = "https://lite.duckduckgo.com/lite/"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )
}


def clean_url(url):
    if not url:
        return ""

    url = url.strip()

    try:
        parsed = urlparse(url)

        if "duckduckgo.com" in parsed.netloc:
            params = parse_qs(parsed.query)

            if "uddg" in params and params["uddg"]:
                return unquote(params["uddg"][0])

    except Exception:
        pass

    return url


def is_ad(text):
    if not text:
        return False

    text_lower = text.lower()

    ad_words = [
        "advertisement",
        "sponsored",
        "quảng cáo",
        "ads by",
    ]

    return any(
        word in text_lower
        for word in ad_words
    )


def parse_results(html, max_results=5):
    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []
    seen_urls = set()

    # DuckDuckGo Lite dùng các link có class result-link
    links = soup.select("a.result-link")

    for link in links:

        if len(results) >= max_results:
            break

        title = link.get_text(
            " ",
            strip=True
        )

        url = clean_url(
            link.get("href", "")
        )

        if not title or not url:
            continue

        if url in seen_urls:
            continue

        if is_ad(title):
            continue

        # Tìm phần mô tả gần kết quả
        text = ""

        parent = link.parent

        if parent:
            parent_text = parent.get_text(
                " ",
                strip=True
            )

            if parent_text:
                text = parent_text

        text = " ".join(
            text.split()
        )

        # Không để title lặp lại trong snippet
        if text.startswith(title):
            text = text[len(title):].strip()

        seen_urls.add(url)

        results.append({
            "title": title,
            "text": text,
            "url": url
        })

    return results


def search_web(query, max_results=5):
    query = query.strip()

    if len(query) < 2:
        return []

    try:
        response = requests.get(
            SEARCH_URL,
            params={
                "q": query
            },
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        return parse_results(
            response.text,
            max_results=max_results
        )

    except requests.exceptions.Timeout:
        return []

    except requests.exceptions.RequestException:
        return []

    except Exception:
        return []


def safe_search(query, max_results=5):
    query = query.strip()

    if len(query) < 2:
        return []

    if len(query) > 300:
        query = query[:300]

    return search_web(
        query,
        max_results=max_results
    )


if __name__ == "__main__":

    print("=" * 50)
    print("MINH MINI - WEB V2.2 TEST")
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