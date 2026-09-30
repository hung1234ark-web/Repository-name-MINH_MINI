import requests


def summarize_results(query, results, config, memory):
    """
    Gửi kết quả tìm kiếm cho Qwen để tóm tắt thành câu trả lời tự nhiên.
    """

    if not results:
        return "Minh không tìm thấy kết quả phù hợp."

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    formatted_results = []

    for i, item in enumerate(results, 1):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        url = item.get("url", "")

        formatted_results.append(
            f"{i}. {title}\n"
            f"Mô tả: {snippet}\n"
            f"Link: {url}"
        )

    search_text = "\n\n".join(formatted_results)

    system_prompt = f"""
Bạn là {assistant_name}, trợ lý riêng của {user_name}.

Nhiệm vụ:
- Đọc các kết quả tìm kiếm trên web.
- Trả lời câu hỏi của {user_name} dựa trên các kết quả đó.
- Không bịa thông tin không có trong kết quả.
- Nếu thông tin chưa đủ để kết luận, nói rõ.
- Trả lời bằng tiếng Việt.
- Ưu tiên câu trả lời ngắn gọn, dễ hiểu.
- Nếu có thông tin quan trọng, có thể liệt kê theo từng ý.
- Không cần đọc lại toàn bộ kết quả tìm kiếm.
"""

    user_prompt = f"""
Câu hỏi của {user_name}:
{query}

Các kết quả tìm kiếm:
{search_text}

Hãy tổng hợp thông tin và trả lời câu hỏi.
"""

    url = config["ollama_url"].rstrip("/") + "/api/chat"

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    response = requests.post(
        url,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"].strip()


if __name__ == "__main__":
    print("web_ai.py đã sẵn sàng.")