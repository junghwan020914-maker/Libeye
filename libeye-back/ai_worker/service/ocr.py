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
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=150)

        if resp.status_code == 404:
            print(f"[Ollama] '{OLLAMA_MODEL_NAME}' 모델 없음")
            return {"call_number": "인식실패(모델없음)", "title": "인식실패"}

        resp.raise_for_status()
        result = resp.json()
        eval_count    = result.get("eval_count", "?")      # 생성한 토큰 수
        prompt_eval   = result.get("prompt_eval_count", "?")  # 입력 토큰 수
        total_dur_ms  = round(result.get("total_duration", 0) / 1e6)  # ns → ms
        print(f"[Ollama] 토큰: 입력={prompt_eval}, 생성={eval_count}, 소요={total_dur_ms}ms")
        return json.loads(result.get("response", "{}"))

    except requests.exceptions.Timeout:
        print(f"[Ollama] OCR 타임아웃 (>{150}s)")
        return {"call_number": "인식실패(타임아웃)", "title": "인식실패"}

    except requests.exceptions.ConnectionError as e:
        print(f"[Ollama] OCR 연결 오류: {e}")
        return {"call_number": "인식실패(연결오류)", "title": "인식실패"}

    except json.JSONDecodeError as e:
        print(f"[Ollama] OCR 응답 JSON 파싱 실패: {e}")
        return {"call_number": "인식실패(파싱오류)", "title": "인식실패"}

    except Exception as e:
        print(f"[Ollama] OCR 예상치 못한 오류 ({type(e).__name__}): {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"  응답 내용: {e.response.text}")
        return {"call_number": "인식실패(알수없음)", "title": "인식실패"}
