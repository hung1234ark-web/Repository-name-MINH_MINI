import requests


def search_web(query):
    """
    Tìm kiếm web thông qua DuckDuckGo Instant Answer API.
    Trả về danh sách kết quả đơn giản cho MINH MINI.
    """

    url = "https://api.duckduckgo.com/"

    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        results = []

        # Kết quả chính
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Kết quả"),
                "text": data["AbstractText"],
                "url": data.get("AbstractURL", "")
            })

        # Các kết quả liên quan
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict):

                text = topic.get("Text")
                first_url = topic.get("FirstURL")

                if text:
                    results.append({
                        "title": text[:100],
                        "text": text,
                        "url": first_url or ""
                    })

            if len(results) >= 5:
                break

        return results

    except requests.exceptions.Timeout:
        return [{
            "title": "Lỗi",
            "text": "Tìm kiếm web phản hồi quá lâu.",
            "url": ""
        }]

    except requests.exceptions.RequestException as e:
        return [{
            "title": "Lỗi kết nối",
            "text": f"Không thể kết nối web: {e}",
            "url": ""
        }]

    except Exception as e:
        return [{
            "title": "Lỗi",
            "text": f"Có lỗi khi tìm kiếm: {e}",
            "url": ""
        }]


def format_results(results):

    if not results:
        return "Không tìm thấy kết quả phù hợp."

    output = []

    for i, result in enumerate(results, 1):

        title = result.get("title", "")
        text = result.get("text", "")
        url = result.get("url", "")

        output.append(
            f"{i}. {title}\n"
            f"   {text}\n"
            f"   {url}"
        )

    return "\n\n".join(output)