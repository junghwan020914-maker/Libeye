import { ref, onUnmounted } from 'vue';
import { cartAPI } from '../api/cartAPI';

export function useCartPolling() {
  const status = ref('PENDING');
  const resultData = ref<any>(null);
  const error = ref<string | null>(null);
  let pollingInterval: number | null = null;

  const startPolling = async (sessionId: number, intervalMs = 2000) => {
    const poll = async () => {
      try {
        const data = await cartAPI.getCartResult(sessionId);
        status.value = data.status;
        
        if (data.status === 'SUCCESS') {
          resultData.value = data;
          stopPolling();
        } else if (data.status === 'FAILED') {
          error.value = '이미지 분석에 실패했습니다.';
          stopPolling();
        }
      } catch (err: any) {
        error.value = err.message || '결과를 불러오는 중 오류가 발생했습니다.';
        stopPolling();
      }
    };

    // 즉시 1회 실행 후 인터벌 설정
    await poll();
    if (status.value === 'PENDING' || status.value === 'PROCESSING') {
      pollingInterval = window.setInterval(poll, intervalMs);
    }
  };

  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  };

  onUnmounted(() => {
    stopPolling();
  });

  return { status, resultData, error, startPolling, stopPolling };
}