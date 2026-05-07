import { api } from './axios';

export const startSession = async (locationId: string, imageBase64: string) => {
  // 💡 HTML의 fetch 로직과 100% 동일한 JSON POST 요청
  const response = await api.post('/api/v1/sessions', {
    location_id: locationId,
    image_base64: imageBase64
  });
  return response.data;
};

export const getSessionResults = async (sessionId: string) => {
  if (!sessionId) throw new Error('세션 ID가 없습니다.');
  const response = await api.get(`/api/v1/sessions/${sessionId}/results`);
  return response.data;
};
