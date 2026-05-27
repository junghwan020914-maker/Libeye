import axios from './axios'; // 기존 설정된 axios 인스턴스 사용

export const cartAPI = {
  // 북카트 이미지 업로드 및 분석 요청
  uploadCartImage: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post('/api/cart/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data; // { session_id: number, status: string }
  },

  // 분석 결과(정렬된 도서 목록) 조회
  getCartResult: async (sessionId: number) => {
    const response = await axios.get(`/api/cart/${sessionId}`);
    return response.data;
  }
};