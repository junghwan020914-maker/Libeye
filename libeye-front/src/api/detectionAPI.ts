// ⚠ 이 모듈은 의도적으로 공유 axios 인스턴스(./axios)가 아닌 fetch()를 사용합니다.
// 공유 인스턴스는 60초 타임아웃과 ngrok 우회 헤더를 추가하는데,
// 이 엔드포인트들은 원래 DetailView에서 raw fetch로 작성되어 있었고
// 런타임 동작을 동일하게 유지해야 하기 때문입니다.

// 도서 검색 (DetailView 수동 교정용 — sessionAPI의 axios 기반 searchBooks와 별개)
export const searchBooksRaw = async (query: string): Promise<any> => {
  const res = await fetch(`/api/v1/search/books?q=${encodeURIComponent(query)}`);
  return res.json();
};

// 장서 DB 강제 매칭
export const forceMatchDetection = (
  sessionId: string | null,
  detectionId: string,
  bookId: string,
): Promise<Response> =>
  fetch(`/api/v1/sessions/${sessionId}/detections/${detectionId}/match`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ book_id: bookId })
  });

// 조치(물리적 이동) 완료 확인
export const verifyDetection = (
  sessionId: string | null,
  detectionId: string,
): Promise<Response> =>
  fetch(`/api/v1/sessions/${sessionId}/detections/${detectionId}/verify`, {
    method: 'PUT'
  });

// 탐지 결과 삭제 (책이 아닌 객체 무시)
export const deleteDetection = (
  sessionId: string | null,
  detectionId: string,
): Promise<Response> =>
  fetch(`/api/v1/sessions/${sessionId}/detections/${detectionId}`, {
    method: 'DELETE'
  });

// 일괄 조치 완료 처리
export const verifyAllDetections = (sessionId: string | null): Promise<Response> =>
  fetch(`/api/v1/sessions/${sessionId}/verify-all`, {
    method: 'PUT'
  });
