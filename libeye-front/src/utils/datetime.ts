// 🚀 추가됨: ISO 타임스탬프를 읽기 좋은 한국 시간 형식(YYYY-MM-DD HH:mm)으로 포맷팅
export const formatDateTime = (isoString: string) => {
  if (!isoString) return '';

  const date = new Date(isoString);
  // 올바른 날짜 형식이 아닐 경우 원본 반환
  if (isNaN(date.getTime())) return isoString;

  const pad = (num: number) => String(num).padStart(2, '0');

  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());

  return `${year}-${month}-${day} ${hours}:${minutes}`;
};
