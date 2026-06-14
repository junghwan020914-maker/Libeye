import json
import time
import requests

from config import OLLAMA_API_URL, OLLAMA_MODEL_NAME

# stream=True에서 timeout은 "청크 사이 간격"만 보므로, 토큰이 계속 나오는
# 폭주는 못 잡는다. 총 경과시간(_WALL_LIMIT)으로 한 OCR 요청의 상한을 둔다.
_TIMEOUT = 150      # (connect/read) 청크 사이 간격 한계
_WALL_LIMIT = 150   # 한 OCR 요청 총 허용 시간(초) — 초과 시 강제 중단

# format=json 모드에서 모델이 EOS를 못 내고 공백/반복 토큰을 무한 생성하는
# 폭주가 있어 생성 토큰 수에 상한을 둔다. 정상 응답(청구기호+제목 JSON)은
# 수십 토큰이면 충분하므로 256이면 넉넉하다.
_NUM_PREDICT = 256

# 폭주는 샘플링에 따른 확률적 현상이라 같은 이미지도 재시도하면 정상 종료할
# 수 있다. num_predict에 걸려 잘린(done_reason=length) 경우에만 재시도한다.
_MAX_RETRIES = 2

_PROMPT = """
You are a library assistant. Examine the image of the book spine.
Extract the 'call_number' and the 'title'.
'call_number' and the 'title' can be in any orientation, partially obscured, or damaged. Do your best to infer them from visible clues.

CRITICAL: The 'call_number' follows specific library cataloging structures. It can include decimal numbers, Korean characters, English alphabets, and volume/copy suffixes.
Examples of valid 'call_number' formats from our library database:
1. Standard Domestic: "001.3 박72ㅂ" or "001.309 성69ㅂ"
2. With Volume/Copy suffix: "001.3 박95ㅁ v.2", "001.3 박819ㄷc.2", or "001.3 백51ㅌ v.1 c.2"
3. Western/Translated Author style: "001.3 A956m강" or "001.3 C284w한"
4. Deep Classification: "001.3028563 최72a"

Always preserve the spaces, dots, and lowercase suffixes (like v.1, c.2) exactly as they appear or should be structured.
If you cannot confidently identify either, return an empty string for that field.

Respond strictly in JSON format like this:
{"call_number": "extracted text", "title": "extracted text"}
DO NOT include any extra notes, descriptions, or comments. Just output the exact JSON.
"""
# num_predict 한도에 걸려 잘린 시도를 나타내는 센티널
_TRUNCATED = object()

# 🚨 2차 시도용 강력한 보정 프롬프트
_RETRY_PROMPT = """
You are an expert library assistant. This is a SECOND ATTEMPT to read a challenging book spine image that failed in the first round.
Examine the image extremely carefully. Even if the text is blurry, small, rotated, or partially damaged, try your absolute best to infer the 'call_number' and 'title'.

Remember, the 'call_number' strictly fits into one of these real patterns:
- "001.3 박72ㅂ" (Standard)
- "001.3 백51ㅌ v.1 c.2" (With Volume/Copy)
- "001.3 A956m강" (Alphabet mixed author code)
- "001.3028563 최72a" (Long decimal classification)

Pay extra attention to small characters like 'v.1', 'c.2', or leading English letters in the author code on the spine label.
Respond strictly in JSON format like this:
{"call_number": "extracted text", "title": "extracted text"}
If you cannot read it at all, return empty strings. DO NOT include any extra notes or explanations.
"""

def extract_text_with_gemma(base64_image: str) -> dict:
    for attempt in range(_MAX_RETRIES + 1):
        # ➔ 수정한 부분: retry_count로 현재 루프의 attempt 번호를 전달합니다.
        result = _request_ocr(base64_image, prompt=_PROMPT, retry_count=attempt)
        if result is not _TRUNCATED:
            return result
        if attempt < _MAX_RETRIES:
            print(f"[Ollama] OCR 재시도 ({attempt + 1}/{_MAX_RETRIES})")
    return {"call_number": "인식실패(생성한도초과)", "title": "인식실패"}


# 미매칭 도서 전용 2차 재인식 함수
def extract_text_with_gemma_retry(base64_image: str) -> dict:
    """1차 매칭 실패 도서를 대상으로 더 엄격하고 정밀한 프롬프트를 사용하여 OCR 재시도"""
    for attempt in range(_MAX_RETRIES + 1):
        # ➔ 수정한 부분: retry_count로 현재 루프의 attempt 번호를 전달합니다.
        result = _request_ocr(base64_image, prompt=_RETRY_PROMPT, retry_count=attempt)
        if result is not _TRUNCATED:
            return result
        if attempt < _MAX_RETRIES:
            print(f"[Ollama] 2차 OCR 내 재시도 ({attempt + 1}/{_MAX_RETRIES})")
    return {"call_number": "2차인식실패(생성한도초과)", "title": "2차인식실패"}

    
def build_ollama_options(retry_count: int) -> dict:
    # 1차 시도 (기본적이고 안정적인 세팅)
    options = {
        "temperature": 0.1,
        "num_predict": _NUM_PREDICT,
        "num_ctx": 4096,  # 멀티모달 OCR은 안전하게 컨텍스트를 늘려 잡는 것이 좋습니다.
    }
    
    # 🚨 2차 시도 (재시도 가동 시) 옵션 동적 변형
    if retry_count > 0:
        options["temperature"] = 0.2            # 창의성/유연성을 미세하게 부여
        options["seed"] = int(time.time())       # 매번 다른 난수 경로를 타도록 설정
        options["min_p"] = 0.05                  # temperature 상승으로 인한 무작위 환각 억제
        options["repeat_penalty"] = 1.25          # 특정 문자 무한 반복 루프 방지
        
    return options


# ➔ 수정한 부분: retry_count 매개변수를 추가하여 NameError를 해결합니다.
def _request_ocr(base64_image: str, prompt: str = _PROMPT, retry_count: int = 0):
    """Ollama에 OCR 1회 요청. num_predict 한도로 잘리면 _TRUNCATED를 반환한다."""
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt, 
        "images": [base64_image],
        "format": "json",
        "stream": True,
        # ➔ 수정한 부분: 인자로 받은 retry_count를 대입합니다.
        "options": build_ollama_options(retry_count=retry_count),
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
        done_reason = None
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
                done_reason = chunk.get("done_reason")
                break

        # 폭주로 잘린 응답은 미완성 JSON이므로 파싱하지 않고 재시도 대상으로 넘긴다
        if done_reason == "length":
            print(f"[Ollama] OCR 생성 한도 초과로 잘림 (num_predict={_NUM_PREDICT})")
            return _TRUNCATED

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