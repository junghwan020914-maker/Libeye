import json
import requests

from config import OLLAMA_API_URL, OLLAMA_MODEL_NAME

# Ollama non-streaming(stream=False) 경로는 멀티모달/대형모델 추론 시
# 응답 전체를 생성할 때까지 데이터 I/O가 멈추는데, 이 침묵 구간을 서버가
# 죽은 연결로 간주해 간헐적으로 500 에러/hang이 발생한다.
# stream=True로 청크를 지속 전송하면 이 문제를 회피할 수 있어
# (커뮤니티 표준 우회법) 백엔드에서 청크를 모아 한 번에 반환한다.
_TIMEOUT = (10, 150)  # (connect, read) — read는 청크 사이 간격 한계

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
        "stream": True,  # 500/hang 회피 — 청크를 받아 아래에서 조립
        "options": {"temperature": 0.1},
    }
    try:
        resp = requests.post(
            OLLAMA_API_URL, json=payload, stream=True, timeout=_TIMEOUT
        )

        if resp.status_code == 404:
            print(f"[Ollama] '{OLLAMA_MODEL_NAME}' 모델 없음")
            return {"call_number": "인식실패(모델없음)", "title": "인식실패"}

        resp.raise_for_status()

        # 스트림으로 받은 청크를 모아 완성된 응답으로 조립
        response_text = ""
        for line in resp.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            if "error" in chunk:
                print(f"[Ollama] OCR 스트림 에러: {chunk['error']}")
                return {"call_number": "인식실패(스트림에러)", "title": "인식실패"}
            response_text += chunk.get("response", "")
            if chunk.get("done"):
                break

        return json.loads(response_text or "{}")

    except requests.exceptions.Timeout:
        print(f"[Ollama] OCR 타임아웃 (read>{_TIMEOUT[1]}s)")
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
