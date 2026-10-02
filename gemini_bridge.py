"""Direct Google AI Studio Gemini bridge for MINH MINI."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_BRIDGE_MODEL", "gemini-3.6-flash")


def _api_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


def health_check() -> Dict[str, Any]:
    key = _api_key()
    return {
        "ok": bool(key),
        "api_key_present": bool(key),
        "adapter_available": True,
        "model": DEFAULT_MODEL,
        "network_checked": False,
        "error": None,
    }


def ask(prompt: str, *, model: Optional[str] = None, timeout: float = 90.0) -> Dict[str, Any]:
    if not isinstance(prompt, str) or not prompt.strip():
        return {"ok": False, "error": "prompt_empty", "text": ""}
    key = _api_key()
    if not key:
        return {"ok": False, "error": "gemini_api_key_missing", "text": ""}
    chosen = model or DEFAULT_MODEL
    url = f"{DEFAULT_BASE_URL}/models/{chosen}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = httpx.post(url, params={"key": key}, json=payload, timeout=timeout)
        if response.status_code != 200:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:2000]
            return {
                "ok": False,
                "error": f"Gemini HTTP {response.status_code}: {detail}",
                "text": "",
                "model": chosen,
            }
        data = response.json()
        parts = ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        text = "".join(
            str(part.get("text", ""))
            for part in parts
            if isinstance(part, dict) and part.get("text") is not None
        )
        return {
            "ok": bool(text),
            "error": None if text else "gemini_empty_response",
            "text": text,
            "model": chosen,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"gemini_request_failed: {exc}",
            "text": "",
            "model": chosen,
        }


if __name__ == "__main__":
    import json
    print(json.dumps(health_check(), ensure_ascii=False))
