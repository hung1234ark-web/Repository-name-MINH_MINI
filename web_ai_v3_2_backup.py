import requests


def summarize_results(query, results, config, memory):
    """
    Tổng hợp kết quả web theo hướng thận trọng:
    - Không biến một nguồn thành kết luận chung.
    - Phân biệt thông tin chắc chắn và thông tin chưa đủ dữ liệu.
    - Giữ lại nguồn để người dùng có thể kiểm tra.
    """

    if not results:
        return "Minh không tìm thấy kết quả phù hợp."

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]

    formatted_results = []

    for i, item in enumerate(results, 1):
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()
        url = item.get("url", "").strip()

        formatted_results.append(
            f"NGUỒN {i}\n"
            f"Tiêu đề: {title}\n"
            f"Nội dung: {snippet}\n"
            f"URL: {url}"
        )

    search_text = "\n\n".join(formatted_results)

    system_prompt = f"""
Bạn là {assistant_name}, trợ lý riêng của {user_name}.

Bạn đang tổng hợp thông tin từ kết quả tìm kiếm web.

QUY TẮC RẤT QUAN TRỌNG:

1. Chỉ sử dụng thông tin xuất hiện trong các kết quả được cung cấp.
2. Không tự bịa số liệu, giá, ngày tháng hoặc thông tin sản phẩm.
3. Không lấy một con số từ một nguồn rồi gọi đó là mức giá chung.
4. Nếu các nguồn có mức giá khác nhau, hãy nói rõ rằng giá giữa các nguồn khác nhau.
5. Nếu chỉ có một nguồn cung cấp con số cụ thể, phải nói rõ đó là thông tin từ nguồn đó.
6. Không biến thông tin quảng cáo thành sự thật chắc chắn.
7. Với giá sản phẩm, hãy dùng cụm "giá tham khảo" nếu dữ liệu chưa đủ để xác định giá hiện tại.
8. Nếu dữ liệu không đủ để trả lời chính xác, hãy nói rõ "chưa đủ dữ liệu".
9. Ưu tiên thông tin cụ thể hơn thông tin chung chung.
10. Trả lời bằng tiếng Việt.
11. Trả lời tự nhiên, ngắn gọn nhưng đủ ý.
12. Nếu có nhiều nguồn đáng chú ý, có thể nêu từng mức hoặc từng thông tin và nguồn tương ứng.
13. Không cần liệt kê toàn bộ kết quả nếu chúng không giúp trả lời câu hỏi.

Câu hỏi của người dùng:
{query}
"""

    user_prompt = f"""
Hãy phân tích các kết quả tìm kiếm dưới đây để trả lời câu hỏi.

{search_text}

Yêu cầu:
- Trả lời trực tiếp câu hỏi.
- Không suy đoán vượt quá dữ liệu.
- Nếu có nhiều mức giá hoặc thông tin khác nhau, hãy phân biệt chúng.
- Nếu dữ liệu chưa đủ, hãy nói rõ.
"""

    url = config["ollama_url"].rstrip("/") + "/api/chat"

    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
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
    print("web_ai.py v3.2 đã sẵn sàng.")