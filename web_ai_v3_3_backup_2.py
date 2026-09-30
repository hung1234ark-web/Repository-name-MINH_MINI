import requests
from datetime import datetime


def get_current_date():
    """Lấy ngày hiện tại từ máy của Lam."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d")


def summarize_results(query, results, config, memory):
    """
    Web AI v3.3
    - Nhận biết ngày hiện tại.
    - Không tự bịa năm/ngày.
    - Phân biệt dữ liệu mới/cũ/chưa rõ ngày.
    - Không biến một nguồn thành kết luận chung.
    """

    if not results:
        return "Minh không tìm thấy kết quả phù hợp."

    user_name = memory["user"]["name"]
    assistant_name = memory["assistant"]["name"]
    current_date = get_current_date()

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

NGÀY HIỆN TẠI CỦA MÁY:
{current_date}

Bạn đang phân tích kết quả tìm kiếm trên web.

QUY TẮC THỜI GIAN:
1. Ngày hiện tại là {current_date}.
2. Không được tự thay đổi ngày hoặc năm hiện tại.
3. Không được nói hiện tại là 2023, 2024, 2025 hoặc năm khác nếu không có bằng chứng rõ ràng.
4. Nếu nguồn có ngày xuất bản/cập nhật, hãy chú ý đến ngày đó.
5. Nếu nguồn không có ngày, không được tự đoán ngày.
6. Nếu dữ liệu quá cũ để trả lời câu hỏi "hiện tại", hãy nói rằng dữ liệu có thể chưa phản ánh giá hiện tại.
7. Nếu không đủ dữ liệu mới để xác định giá hiện tại, phải nói rõ "chưa đủ dữ liệu mới".
8. Không được bịa ngày tháng.

QUY TẮC THÔNG TIN:
1. Chỉ sử dụng thông tin xuất hiện trong kết quả tìm kiếm.
2. Không bịa giá, số liệu, sản phẩm hoặc nguồn.
3. Không lấy một con số từ một nguồn rồi gọi đó là giá chung.
4. Nếu nhiều nguồn có mức giá khác nhau, hãy nói rõ.
5. Nếu chỉ một nguồn có số liệu cụ thể, phải nói rõ đó là thông tin từ nguồn đó.
6. Không biến quảng cáo thành sự thật chắc chắn.
7. Với giá sản phẩm/nông sản, dùng "giá tham khảo" nếu dữ liệu chưa đủ.
8. Nếu không đủ dữ liệu, nói thẳng là chưa đủ dữ liệu.
9. Không suy đoán để lấp khoảng trống thông tin.
10. Trả lời bằng tiếng Việt.
11. Trả lời tự nhiên và ngắn gọn.
"""

    user_prompt = f"""
Câu hỏi của {user_name}:
{query}

Ngày hiện tại:
{current_date}

Các kết quả tìm kiếm:
{search_text}

Hãy trả lời câu hỏi dựa trên các nguồn trên.

Đặc biệt:
- Nếu người dùng hỏi "hiện tại", ưu tiên dữ liệu mới.
- Kiểm tra xem nguồn có ngày tháng hay không.
- Nếu không có đủ dữ liệu mới, nói rõ điều đó.
- Không được tự tạo ra ngày hoặc năm.
- Nếu có nhiều mức giá, nêu các mức được nguồn cung cấp thay vì tự tính một mức chung.
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
    print("web_ai.py v3.3 đã sẵn sàng.")
    print("Ngày hiện tại:", get_current_date())