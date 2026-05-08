import axios from 'axios';

export const api = axios.create({
  baseURL: '/api', 
  timeout: 60000, // AI 모델 처리가 오래 걸릴 수 있으므로 60초 대기
  headers: {
    'Content-Type': 'application/json',
    // [필수] ngrok 무료 버전의 브라우저 경고창 차단을 우회하는 헤더
    'ngrok-skip-browser-warning': '69420'
  },
});