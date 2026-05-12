<script setup lang="ts">
import { ref } from 'vue';
import { startSession } from '../../api/sessionAPI';
import { useAnalysisPolling } from '../../composables/useAnalysisPolling';
import ResultStatusList from '../dashboard/ResultStatusList.vue';

const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);
const uploadStatus = ref<string>('');
const currentSessionId = ref<string | null>(null);

const { data: sessionData, isError } = useAnalysisPolling(currentSessionId);

const triggerCamera = () => {
  fileInput.value?.click();
};

// 💡 HTML(new_dash2)의 동작 방식과 100% 동일한 원본 변환 로직
const fileToPureBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file); // 화질 손상 없는 원본 Base64 추출
    reader.onload = () => {
      const result = reader.result as string;
      // 파이썬 처리를 위해 'data:image/...;base64,' 접두사만 안전하게 잘라냅니다.
      const base64String = result.includes(',') ? result.split(',')[1] : result;
      resolve(base64String);
    };
    reader.onerror = (error) => reject(error);
  });
};

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  
  if (!file) return;

  try {
    isUploading.value = true;
    uploadStatus.value = '이미지 준비 중...';
    currentSessionId.value = null;

    // 캔버스 없이 파일 원본을 Base64로 즉시 변환
    const base64Image = await fileToPureBase64(file);

    uploadStatus.value = 'AI 서버로 전송 중...';
    
    // seed.py 의 실제 위치 ID (LOC-A-1-3)
    const response = await startSession('LOC-A-1-3', base64Image);

    currentSessionId.value = response.session_id;
    uploadStatus.value = '전송 완료! AI가 도서를 분석 중입니다...';

  } catch (err: any) {
    console.error('🔥 업로드 에러:', err);
    uploadStatus.value = '업로드 실패. 네트워크를 확인해주세요.';
  } finally {
    isUploading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
};
</script>

<template>
  <div class="flex flex-col items-center justify-center p-8 bg-white rounded-3xl shadow-xl border border-slate-100">
    <div v-if="!currentSessionId" class="w-full">
      <div class="mb-6 text-center">
        <h2 class="text-2xl font-black text-slate-800">서가 사진 촬영</h2>
        <p class="text-slate-400 mt-2">책등이 잘 보이도록 정면에서 촬영해주세요.</p>
      </div>

      <input type="file" accept="image/*" capture="environment" ref="fileInput" class="hidden" @change="handleFileSelect" />

      <button 
        @click="triggerCamera" 
        :disabled="isUploading"
        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-5 px-10 rounded-2xl shadow-lg transition-all active:scale-95 disabled:opacity-50"
      >
        <span v-if="!isUploading">📸 카메라 켜기 / 사진 선택</span>
        <span v-else>⏳ 처리 중...</span>
      </button>

      <div v-if="uploadStatus" class="mt-6 text-sm font-bold text-blue-500 text-center animate-pulse">
        {{ uploadStatus }}
      </div>
    </div>

    <!-- 폴링 및 결과 UI -->
    <div v-else class="w-full">
      <div v-if="(sessionData?.status?.toUpperCase() !== 'COMPLETED' && sessionData?.status?.toUpperCase() !== 'SUCCESS') && !isError" class="flex flex-col items-center py-12">
        <div class="w-12 h-12 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-4"></div>
        <p class="text-blue-600 font-bold animate-pulse">AI 분석 중입니다 ({{ sessionData?.status || 'PENDING' }})</p>
      </div>
      
      <div v-else-if="isError" class="text-center py-10">
        <p class="text-red-500 font-bold text-lg">서버 연결 오류</p>
        <button @click="currentSessionId = null" class="mt-4 text-slate-500 underline text-sm">다시 시도하기</button>
      </div>

      <div v-else-if="sessionData">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-black text-slate-800">분석 완료</h2>
        </div>
        <ResultStatusList :detections="sessionData.detections" />
        <button @click="currentSessionId = null" class="mt-8 w-full py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl">
          새로운 사진 촬영
        </button>
      </div>
    </div>
  </div>
</template>
