<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { startSession } from '../api/sessionAPI';

const router = useRouter();
const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const previewUrl = ref<string | null>(null);
const isCameraReady = ref(false);
const isCameraError = ref(false);
const isUploading = ref(false);
const currentStream = ref<MediaStream | null>(null);

const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    currentStream.value = stream;
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      isCameraReady.value = true;
    }
  } catch (err) {
    console.error('Camera access error:', err);
    isCameraError.value = true;
  }
};

const stopCamera = () => {
  if (currentStream.value) {
    currentStream.value.getTracks().forEach(t => t.stop());
    currentStream.value = null;
  }
};

const takePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return;
  
  const video = videoRef.value;
  const canvas = canvasRef.value;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  ctx.drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
  previewUrl.value = dataUrl;
  
  // Stop camera stream to freeze frame
  stopCamera();
  
  // Upload logic
  isUploading.value = true;
  try {
    const base64Image = dataUrl.split(',')[1];
    const response = await startSession('LOC-A-1-3', base64Image);
    const sessionId = response.session_id;
    
    // Move to detail view with sessionId
    router.push({ name: 'detail', query: { sessionId } });
  } catch (err) {
    console.error('Upload error:', err);
    alert('업로드 중 오류가 발생했습니다.');
    isUploading.value = false;
    previewUrl.value = null;
    startCamera(); // restart camera
  }
};

const simulateCapture = async () => {
  // In case of error (e.g. desktop without camera), we simulate capture with an empty white image for testing
  isUploading.value = true;
  try {
    // Generate dummy 1x1 white base64 image
    const dummyBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=";
    const response = await startSession('LOC-A-1-3', dummyBase64);
    const sessionId = response.session_id;
    router.push({ name: 'detail', query: { sessionId } });
  } catch (err) {
    console.error('Upload error:', err);
    alert('업로드 중 오류가 발생했습니다.');
    isUploading.value = false;
  }
};

onMounted(() => {
  startCamera();
});

onBeforeUnmount(() => {
  stopCamera();
});
</script>

<template>
  <main class="flex-col h-full bg-black relative z-30 flex animate-fade-in">
    <div class="absolute top-0 w-full z-20 p-4 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent pb-10 text-white">
      <button @click="router.push('/')" class="text-2xl px-2">◀</button>
      <div class="text-center">
        <h1 class="text-sm font-bold">인문과학실 A-2 서가</h1>
        <p class="text-[10px] text-white/70">책등 수평을 맞춰주세요</p>
      </div>
      <button class="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-xl active:bg-white/40">⚡</button>
    </div>

    <div class="flex-1 relative overflow-hidden flex items-center justify-center bg-stone-800">
      <video v-show="!previewUrl && !isCameraError" ref="videoRef" autoplay playsinline class="absolute w-full h-full object-cover"></video>
      <canvas ref="canvasRef" class="hidden"></canvas>
      <img v-if="previewUrl" :src="previewUrl" class="absolute w-full h-full object-cover z-10" />
      
      <div v-if="!previewUrl && !isCameraError" class="absolute inset-15 border-2 border-white/40 shadow-[0_0_0_9999px_rgba(0,0,0,0.5)] flex flex-col justify-evenly items-center pointer-events-none z-10" style="inset: 15%">
        <div class="w-full h-px bg-white/30 absolute top-1/3"></div>
        <div class="w-full h-px bg-white/30 absolute top-2/3"></div>
        <div class="absolute w-px h-full bg-white/30"></div>
        <div class="w-4 h-4 border-l-2 border-t-2 border-[#2E7D32] absolute top-0 left-0"></div>
        <div class="w-4 h-4 border-r-2 border-t-2 border-[#2E7D32] absolute top-0 right-0"></div>
        <div class="w-4 h-4 border-l-2 border-b-2 border-[#2E7D32] absolute bottom-0 left-0"></div>
        <div class="w-4 h-4 border-r-2 border-b-2 border-[#2E7D32] absolute bottom-0 right-0"></div>
      </div>

      <div v-if="isCameraError" class="absolute inset-0 bg-stone-900 z-20 flex flex-col items-center justify-center p-6 text-center">
        <span class="text-4xl mb-4">🚫</span>
        <h3 class="text-white font-bold mb-2">카메라 권한 필요</h3>
        <p class="text-stone-400 text-xs mb-6">테스트 환경에서는 가상 캡처를 사용합니다.</p>
        <button @click="simulateCapture" class="px-6 py-3 bg-stone-700 text-white rounded-xl font-bold active:bg-stone-600">가상 이미지 캡처</button>
      </div>
    </div>

    <div class="h-32 bg-black flex items-center justify-around px-6 shrink-0 relative z-20">
      <button class="w-10 h-10 text-white/80 text-2xl">🖼</button>
      <button @click="takePhoto" :disabled="isUploading || isCameraError" class="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center bg-white/20 active:scale-95 transition-all disabled:opacity-50">
        <div class="w-12 h-12 rounded-full bg-white"></div>
      </button>
      <button class="w-10 h-10 text-white/80 text-2xl">🔄</button>
    </div>

    <!-- 로딩 오버레이 -->
    <div v-if="isUploading" class="absolute inset-0 bg-stone-900/90 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
      <div class="w-16 h-16 border-4 border-stone-600 border-t-green-500 rounded-full animate-spin mb-6"></div>
      <h2 class="text-white font-extrabold text-lg tracking-wide animate-pulse">Vision AI 분석 중...</h2>
      <p class="text-stone-400 text-xs mt-2">청구기호 해독 및 배가 상태 비교</p>
    </div>
  </main>
</template>
