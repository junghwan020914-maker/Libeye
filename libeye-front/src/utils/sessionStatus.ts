// 서버 응답이 아직 오지 않은(분석 중) 세션 판별
// ScanSession.status: PENDING / PROCESSING / COMPLETED / FAILED
export const isAnalyzing = (item: any) => {
  const s = (item?.status ?? '').toString().toUpperCase();
  return s !== 'COMPLETED' && s !== 'FAILED';
};

// 상태 우선순위: 분석 중 → 실패 → 미결 → 완료
export const statusOf = (item: any): 'analyzing' | 'failed' | 'unresolved' | 'done' => {
  if (isAnalyzing(item)) return 'analyzing';
  if ((item?.status ?? '').toString().toUpperCase() === 'FAILED') return 'failed';
  if ((item?.error_count ?? 0) > 0) return 'unresolved';
  return 'done';
};
