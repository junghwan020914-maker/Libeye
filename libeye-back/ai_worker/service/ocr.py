import json
import time
import requests

from config import OLLAMA_API_URL, OLLAMA_MODEL_NAME

# stream=True에서 timeout은 "청크 사이 간격"만 보므로, 토큰이 계속 나오는
# 폭주는 못 잡는다. 총 경과시간(_WALL_LIMIT)으로 한 OCR 요청의 상한을 둔다.
_TIMEOUT = 150      # (connect/read) 청크 사이 간격 한계
_WALL_LIMIT = 150   # 한 OCR 요청 총 허용 시간(초) — 초과 시 강제 중단

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
        "stream": True,
        "options": {"temperature": 0.1},
    }
    start = time.time()
    try:
        resp = requests.post(
            OLLAMA_API_URL, json=payload, stream=True, timeout=_TIMEOUT
        )

        if resp.status_code == 404:
            print(f"[Ollama] '{OLLAMA_MODEL_NAME}' 모델 없음")
            return {"call_number": "인식실패(모델없음)", "title": "인식실패"}

        resp.raise_for_status()

        # 스트림 청크를 모아 완성된 응답으로 조립
        response_text = ""
        for line in resp.iter_lines():
            if not line:
                continue

            # 토큰 폭주 안전망: 총 시간 초과 시 강제 중단
            if time.time() - start > _WALL_LIMIT:
                print(f"[Ollama] OCR 강제 중단: {_WALL_LIMIT}s 초과")
                resp.close()
                return {"call_number": "인식실패(시간초과)", "title": "인식실패"}

            chunk = json.loads(line)
            if "error" in chunk:
                print(f"[Ollama] OCR 스트림 에러: {chunk['error']}")
                return {"call_number": "인식실패(스트림에러)", "title": "인식실패"}
            response_text += chunk.get("response", "")
            if chunk.get("done"):
                break

        return json.loads(response_text or "{}")

    except requests.exceptions.Timeout:
        print(f"[Ollama] OCR 타임아웃 (>{_TIMEOUT}s)")
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
