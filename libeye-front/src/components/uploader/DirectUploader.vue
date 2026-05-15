<script setup lang="ts">
import { ref } from 'vue';
import { startSession } from '../../api/sessionAPI';
import { useAnalysisPolling } from '../../composables/useAnalysisPolling';
import ResultStatusList from '../dashboard/ResultStatusList.vue';

const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);
const uploadStatus = ref<string>('');
const currentSessionId = ref<string | null>(null);

// 🚨 추가됨: 여러 파일과 썸네일을 관리하는 상태 배열
const selectedFiles = ref<File[]>([]);
const previewUrls = ref<string[]>([]);

const { data: sessionData, isError } = useAnalysisPolling(currentSessionId);

const triggerCamera = () => {
  fileInput.value?.click();
};

// 🚨 수정됨: Base64 변환 대신 File 객체를 배열에 순서대로 누적하고 썸네일 생성
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files || []); // multiple 속성 지원

  if (files.length === 0) return;

  files.forEach(file => {
    selectedFiles.value.push(file);
    // 미리보기를 위한 임시 URL 생성 (브라우저 메모리 사용)
    previewUrls.value.push(URL.createObjectURL(file)); 
  });

  // 동일한 파일을 다시 선택할 수 있도록 input 초기화
  if (fileInput.value) fileInput.value.value = '';
};

// 🚨 추가됨: 잘못 찍은 사진 삭제 기능 (배열에서 제거)
const removeFile = (index: number) => {
  URL.revokeObjectURL(previewUrls.value[index]); // 메모리 누수 방지
  selectedFiles.value.splice(index, 1);
  previewUrls.value.splice(index, 1);
};

// 🚨 수정됨: 누적된 파일 배열을 통째로 서버에 전송
const submitFiles = async () => {
  if (selectedFiles.value.length === 0) return;

  try {
    isUploading.value = true;
    uploadStatus.value = '이미지 서버로 전송 중...';
    currentSessionId.value = null;

    // seed.py 의 실제 위치 ID (LOC-A-1-3)
    const response = await startSession('LOC-A-1-3', selectedFiles.value);

    currentSessionId.value = response.session_id;
    uploadStatus.value = '전송 완료! AI가 도서를 분석 중입니다...';

    // 전송 완료 후 대기열 초기화
    selectedFiles.value = [];
    previewUrls.value.forEach(url => URL.revokeObjectURL(url));
    previewUrls.value = [];

  } catch (err: any) {
    console.error('🔥 업로드 에러:', err);
    uploadStatus.value = '업로드 실패. 네트워크를 확인해주세요.';
  } finally {
    isUploading.value = false;
  }
};
</script>

<template>
  <div class="flex flex-col items-center justify-center p-8 bg-white rounded-3xl shadow-xl border border-slate-100">
    <div v-if="!currentSessionId" class="w-full">
      <div class="mb-6 text-center">
        <h2 class="text-2xl font-black text-slate-800">서가 사진 촬영</h2>
        <p class="text-slate-400 mt-2">왼쪽부터 차례대로 사진을 추가해주세요.</p>
      </div>

      <input type="file" accept="image/*" capture="environment" multiple ref="fileInput" class="hidden" @change="handleFileSelect" />

      <div v-if="previewUrls.length > 0" class="flex gap-4 overflow-x-auto pb-4 mb-6 scrollbar-hide">
        <div v-for="(url, index) in previewUrls" :key="index" class="relative min-w-[120px] h-[160px] flex-shrink-0 border-2 border-slate-200 rounded-xl overflow-hidden group">
          <img :src="url" class="w-full h-full object-cover" />
          <div class="absolute top-0 left-0 bg-black/60 text-white text-xs font-bold px-2 py-1 rounded-br-lg">
            {{ index + 1 }}
          </div>
          <button @click="removeFile(index)" class="absolute top-2 right-2 bg-red-500 text-white p-1.5 rounded-full shadow-md hover:bg-red-600 transition-colors">
            ✕
          </button>
        </div>
      </div>

      <div class="flex flex-col gap-3">
        <button 
          @click="triggerCamera" 
          :disabled="isUploading"
          class="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-4 px-10 rounded-2xl shadow-sm transition-all active:scale-95 disabled:opacity-50"
        >
          ➕ 사진 추가하기
        </button>

        <button 
          v-if="selectedFiles.length > 0"
          @click="submitFiles" 
          :disabled="isUploading"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-5 px-10 rounded-2xl shadow-lg transition-all active:scale-95 disabled:opacity-50"
        >
          <span v-if="!isUploading">🚀 {{ selectedFiles.length }}장 분석 시작</span>
          <span v-else>⏳ 업로드 중...</span>
        </button>
      </div>

      <div v-if="uploadStatus" class="mt-6 text-sm font-bold text-blue-500 text-center animate-pulse">
        {{ uploadStatus }}
      </div>
    </div>

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
          새로운 구역 촬영
        </button>
      </div>
    </div>
  </div>
</template>
