import { api } from './axios';

// 🚨 수정됨: imageBase64(string) 대신 files(File 배열)을 받도록 변경
export const startSession = async (locationId: string, files: File[]) => {
  const formData = new FormData();
  formData.append('location_id', locationId);
  
  // 백엔드의 `files: List[UploadFile] = File(...)` 파라미터에 맞추어 여러 파일을 동일한 키('files')로 추가
  files.forEach(file => {
    formData.append('files', file);
  });

  // axios가 FormData를 전송할 때 자동으로 적절한 boundary와 함께 Content-Type을 설정합니다.
  const response = await api.post('/v1/sessions', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getSessionResults = async (sessionId: string) => {
  if (!sessionId) throw new Error('세션 ID가 없습니다.');
  const response = await api.get(`/v1/sessions/${sessionId}/results`);
  return response.data;
};

export const getLocations = async () => {
  const response = await api.get('/v1/locations');
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get('/v1/sessions/history');
  return response.data;
};

export const getMapStatus = async () => {
  const response = await api.get('/v1/map/status');
  return response.data;
};

export const getAnalytics = async () => {
  const response = await api.get('/v1/analytics/dashboard');
  return response.data;
};
