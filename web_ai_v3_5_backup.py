import requests
from datetime import datetime


def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")


def summarize_results(query, results, config, memory):

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

Ngày hiện tại của máy:
{current_date}

Bạn phân tích kết quả tìm kiếm web.

QUY TẮC BẮT BUỘC:

1. Chỉ sử dụng thông tin có trong các nguồn được cung cấp.
2. Không bịa thông tin.
3. Không tự suy đoán dữ liệu còn thiếu.
4. Không lấy một con số từ một nguồn rồi gọi đó là kết luận chung.
5. Nếu các nguồn có giá khác nhau, phải giữ riêng từng mức giá.
6. Không tự chọn giá thấp nhất hoặc cao nhất.
7. Không tính giá trung bình nếu nguồn không cung cấp.
8. Không gọi một mức giá là "giá hiện tại" nếu dữ liệu chưa đủ.
9. Không gọi giá là "giá chính thức" nếu nguồn không nói rõ.
10. Không gọi giá là "giá thị trường" nếu nguồn không chứng minh.
11. Giá khuyến mãi phải được ghi rõ là giá khuyến mãi.
12. Giá của một cửa hàng không được biến thành giá toàn thị trường.

QUY TẮC THỜI GIAN:

- Ngày hiện tại là {current_date}.
- Không tự tạo ngày tháng.
- Không lấy năm trong tiêu đề để kết luận đó là ngày cập nhật.
- Nếu nguồn không có ngày rõ ràng, phải nói dữ liệu không có ngày rõ ràng.
- Nếu dữ liệu chưa đủ mới, phải nói rõ giới hạn.

QUY TẮC GIÁ:

Nếu có nhiều mức giá khác nhau rõ rệt:

- Nêu từng mức giá.
- Gắn từng mức với nguồn tương ứng.
- Giữ nguyên trạng thái khuyến mãi nếu có.
- Không chọn một mức làm giá hiện tại.
- Kết luận rằng chưa đủ dữ liệu để xác định một mức giá hiện tại duy nhất.

Nếu chỉ có một mức giá:

- Nói đó là mức giá được nguồn cung cấp.
- Không tự gọi đó là giá thị trường chung.

CÁCH TRẢ LỜI:

- Tiếng Việt.
- Ngắn gọn.
- Tự nhiên.
- Thông tin quan trọng trước.
- Không suy đoán để lấp khoảng trống.

Khi các nguồn mâu thuẫn về giá, ưu tiên dạng:

"Các nguồn hiện cho mức giá khác nhau:
- [mức giá] — [nguồn/tình trạng]
- [mức giá] — [nguồn/tình trạng]

Chưa đủ dữ liệu để xác định một mức giá hiện tại duy nhất."
"""

    user_prompt = f"""
Câu hỏi của {user_name}:
{query}

Ngày hiện tại:
{current_date}

Kết quả tìm kiếm:
{search_text}

Hãy trả lời chỉ dựa trên các nguồn trên.

Kiểm tra trước khi trả lời:

- Có bao nhiêu mức giá?
- Các mức giá có khác nhau không?
- Mức nào là khuyến mãi?
- Nguồn nào cung cấp từng mức?
- Nguồn có ngày rõ ràng không?
- Có đủ dữ liệu để gọi là giá hiện tại không?

Nếu có nhiều mức giá mâu thuẫn:
phải nêu từng mức và không được chọn một mức làm giá hiện tại.

Không được bịa thông tin.
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
    print("web_ai.py v3.5 đã sẵn sàng.")
    print("Ngày hiện tại:", get_current_date())