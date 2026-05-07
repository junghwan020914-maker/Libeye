import axios from 'axios';

export const api = axios.create({
  // 💡 백엔드 도커가 돌아가고 있는 정확한 주소
  baseURL: 'http://localhost:8000', 
  timeout: 60000, // AI 모델 처리가 오래 걸릴 수 있으므로 넉넉하게 60초로 늘려줍니다.
  headers: {
    'Content-Type': 'application/json',
  },
});
