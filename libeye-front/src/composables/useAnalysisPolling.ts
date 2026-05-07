import { useQuery } from '@tanstack/vue-query';
import { computed, type Ref } from 'vue';
import { getSessionResults } from '../api/sessionAPI';
import type { SessionStatusResponse } from '../types/session';

// 💡 매개변수로 문자열이 아닌 Vue의 반응형 객체(Ref)를 받습니다.
export function useAnalysisPolling(sessionId: Ref<string | null>) {
  return useQuery<SessionStatusResponse, Error>({
    // queryKey에 Ref를 넣으면, sessionId.value가 바뀔 때마다 알아서 감지합니다.
    queryKey: ['session', sessionId],
    
    queryFn: () => {
      if (!sessionId.value) throw new Error("No session ID provided");
      return getSessionResults(sessionId.value);
    },
    
    // sessionId 값이 존재할 때만 폴링이 켜집니다.
    enabled: computed(() => !!sessionId.value),
    
    refetchInterval: (query) => {
      const currentStatus = query.state.data?.status?.toUpperCase();
      
      // 상태가 완료, 성공, 에러 중 하나면 폴링을 멈춥니다.
      if (currentStatus === 'COMPLETED' || currentStatus === 'SUCCESS' || currentStatus === 'ERROR' || currentStatus === 'FAILED') {
        return false; 
      }
      return 2000; // 그 외(PENDING 등)에는 2초마다 다시 요청
    },
  });
}
