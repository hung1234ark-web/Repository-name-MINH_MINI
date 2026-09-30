import json
import urllib.error
import urllib.request
from typing import Any, Optional


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:1.7b"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def build_system_prompt() -> str:
    return (
        "Bạn là Minh, trợ lý AI cục bộ của Lam trong dự án MINH MINI. "
        "Bạn đang xử lý hội thoại thông thường, không phải nhiệm vụ phân tích nguồn web. "
        "Hãy trả lời tự nhiên, ngắn gọn, thân thiện và đúng câu hỏi. "
        "LUÔN trả lời bằng tiếng Việt khi Lam đang giao tiếp bằng tiếng Việt. "
        "Không tự chuyển sang tiếng Anh trừ khi Lam yêu cầu rõ ràng. "
        "Nếu Lam dùng tiếng Anh và không yêu cầu ngôn ngữ cụ thể, có thể trả lời bằng tiếng Anh. "
        "Không được nói rằng cần nguồn dữ liệu hoặc nguồn web nếu người dùng chỉ đang trò chuyện. "
        "Không được tự nhận đã thực hiện hành động trên máy tính nếu hệ thống chưa thực hiện hành động đó."
    )


def get_ollama_config() -> tuple[str, str]:
    try:
        import web_ai

        getter = getattr(web_ai, "get_ollama_config", None)

        if callable(getter):
            result = getter()

            if isinstance(result, (tuple, list)) and len(result) >= 2:
                url = clean_text(result[0])
                model = clean_text(result[1])

                if url and model:
                    return url, model

    except Exception:
        pass

    return DEFAULT_OLLAMA_URL, DEFAULT_MODEL


def extract_message_from_result(data: Any) -> str:
    if not isinstance(data, dict):
        return ""

    message = data.get("message")

    if isinstance(message, dict):
        content = message.get("content")

        if content:
            return clean_text(content)

    response = data.get("response")

    if response:
        return clean_text(response)

    return ""


def call_chat_ollama(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    timeout: int = 120,
) -> str:

    prompt = clean_text(prompt)

    if not prompt:
        return "Lam chưa nhập nội dung để Minh trả lời."

    url, model = get_ollama_config()

    endpoint = url.rstrip("/")

    if not endpoint.endswith("/api/chat"):
        endpoint += "/api/chat"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt or build_system_prompt(),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
    }

    body = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )

        data = json.loads(raw)

        answer = extract_message_from_result(data)

        if answer:
            return answer

        return "Minh chưa nhận được nội dung trả lời từ Ollama."

    except urllib.error.HTTPError as exc:
        return f"Ollama trả về lỗi HTTP {exc.code}."

    except urllib.error.URLError:
        return (
            "Minh chưa kết nối được với Ollama. "
            "Lam kiểm tra Ollama đang chạy giúp Minh nhé."
        )

    except TimeoutError:
        return "Ollama phản hồi quá lâu nên Minh dừng yêu cầu này."

    except Exception as exc:
        return f"Chat handler gặp lỗi: {type(exc).__name__}: {exc}"


def handle_chat(
    message: str = "",
    prompt: str = "",
    query: str = "",
    decision: Any = None,
    **kwargs: Any,
) -> str:

    text = clean_text(prompt)

    if not text:
        text = clean_text(message)

    if not text:
        text = clean_text(query)

    if not text and decision is not None:
        text = clean_text(
            getattr(decision, "original_text", "")
            or getattr(decision, "normalized_text", "")
            or getattr(decision, "query", "")
        )

    return call_chat_ollama(text)


def chat(
    message: str = "",
    prompt: str = "",
    query: str = "",
    decision: Any = None,
    **kwargs: Any,
) -> str:

    return handle_chat(
        message=message,
        prompt=prompt,
        query=query,
        decision=decision,
        **kwargs,
    )


def self_check() -> bool:
    checks = {
        "clean_text": callable(clean_text),
        "build_system_prompt": callable(build_system_prompt),
        "get_ollama_config": callable(get_ollama_config),
        "extract_message_from_result": callable(extract_message_from_result),
        "call_chat_ollama": callable(call_chat_ollama),
        "handle_chat": callable(handle_chat),
        "chat": callable(chat),
    }

    for name, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")

    return all(checks.values())


if __name__ == "__main__":
    ok = self_check()
    print(
        "\n>>> CHAT HANDLER SELF CHECK: "
        + ("PASS" if ok else "FAIL")
    )
