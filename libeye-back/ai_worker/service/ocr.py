import json
import requests

from config import OLLAMA_API_URL, OLLAMA_MODEL_NAME

_PROMPT = """
You are a library assistant. Examine the image of the book spine.
Extract the 'call_number' (e.g., 813.6 김12가) and the 'title'.
Respond strictly in JSON format like this:
{"call_number": "extracted text", "title": "extracted text"}
If you cannot read it, return empty strings.
DO NOT include any extra notes, descriptions, or comments about text orientation (e.g., 'Note: Title is vertical'). Just output the exact text you see.
"""


def extract_text_with_gemma(base64_image: str) -> dict:
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": _PROMPT,
        "images": [base64_image],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        # 26B 모델 Cold Start를 고려해 timeout 5분
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=300)

        if resp.status_code == 404:
            print(f"[Ollama] '{OLLAMA_MODEL_NAME}' 모델 없음")
            return {"call_number": "인식실패(모델없음)", "title": "인식실패"}

        resp.raise_for_status()
        return json.loads(resp.json().get("response", "{}"))

    except Exception as e:
        print(f"[Ollama] OCR 오류: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"  응답 내용: {e.response.text}")
        return {"call_number": "인식실패(통신오류)", "title": "인식실패"}
