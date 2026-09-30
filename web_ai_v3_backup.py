from datetime import datetime


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")


def clean_text(text):
    if text is None:
        return ""

    return " ".join(str(text).split())


def format_source(result, index):
    title = clean_text(result.get("title", ""))
    snippet = clean_text(result.get("snippet", ""))
    url = clean_text(result.get("url", ""))

    parts = []

    if title:
        parts.append(title)

    if snippet:
        parts.append(snippet)

    if url:
        parts.append(url)

    if not parts:
        return f"[Nguồn {index}] Không có nội dung."

    return f"[Nguồn {index}] " + " — ".join(parts)


def build_source_text(results):
    if not results:
        return "Không có nguồn nào được cung cấp."

    lines = []

    for index, result in enumerate(results, start=1):
        lines.append(format_source(result, index))

    return "\n".join(lines)


def summarize_results(query, results, config=None, memory=None):
    """
    Tổng hợp kết quả web một cách thận trọng.

    Quy tắc:
    - Chỉ sử dụng thông tin có trong results.
    - Không tự bịa dữ liệu.
    - Không tự chọn một mức giá nếu các nguồn mâu thuẫn.
    - Không tự biến giá khuyến mãi thành giá thông thường.
    - Không tự tạo ngày tháng nếu nguồn không cung cấp.
    """

    query = clean_text(query)

    if not results:
        return "Minh không tìm thấy kết quả phù hợp."

    source_lines = []

    for index, result in enumerate(results, start=1):
        title = clean_text(result.get("title", ""))
        snippet = clean_text(result.get("snippet", ""))
        url = clean_text(result.get("url", ""))

        if title or snippet:
            text = ""

            if title:
                text += title

            if snippet:
                if text:
                    text += " — "
                text += snippet

            source_lines.append(
                f"- {text} [Nguồn {index}]"
            )

        elif url:
            source_lines.append(
                f"- {url} [Nguồn {index}]"
            )

    if not source_lines:
        return "Minh tìm được nguồn nhưng chưa có đủ nội dung để tổng hợp."

    query_lower = query.lower()

    price_words = [
        "giá",
        "bao nhiêu",
        "giá bao nhiêu",
        "price",
        "cost",
    ]

    is_price_query = any(
        word in query_lower
        for word in price_words
    )

    # Với câu hỏi giá, không tự chọn một con số
    # nếu dữ liệu có khả năng là nhiều loại giá khác nhau.
    if is_price_query:
        text = "\n".join(source_lines)

        return (
            "Minh đã kiểm tra các nguồn tìm được.\n\n"
            f"Câu hỏi: {query}\n\n"
            "Thông tin từ các nguồn:\n"
            f"{text}\n\n"
            "Minh chỉ dùng những thông tin có trong nguồn và "
            "không tự khẳng định một mức giá duy nhất nếu các nguồn "
            "không đủ thống nhất."
        )

    # Với câu hỏi thông thường, trình bày các nguồn tìm được
    # thay vì bịa thêm thông tin ngoài kết quả.
    text = "\n".join(source_lines)

    return (
        "Minh đã kiểm tra thông tin trên web.\n\n"
        f"Câu hỏi: {query}\n\n"
        "Các nguồn tìm được:\n"
        f"{text}"
    )