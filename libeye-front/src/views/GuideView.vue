<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const videoRef = ref<HTMLVideoElement | null>(null);
let stream: MediaStream | null = null;

// 실전 감각을 위해 후면 카메라를 임시로 켜서 프리뷰를 제공합니다.
const startCameraPreview = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    });
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
    }
  } catch (err) {
    console.error('카메라 접근 실패:', err);
    // 카메라 권한이 없는 경우를 위한 에러 처리 방어 로직
  }
};

const stopCameraPreview = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
};

onMounted(() => {
  startCameraPreview();
});

onBeforeUnmount(() => {
  stopCameraPreview();
});
</script>

<template>
  <main class="flex-col h-full bg-stone-900 relative flex animate-fade-in overflow-hidden">
    <header class="absolute top-0 left-0 right-0 z-20 px-4 py-3 flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent">
      <div class="flex items-center">
        <button @click="router.back()" class="p-2 text-white text-xl font-bold mr-2 active:scale-90 transition-transform">◀</button>
        <div>
          <h1 class="text-base font-extrabold text-white">촬영 가이드</h1>
          <p class="text-[10px] font-medium text-stone-300">AI 인식률을 높이는 실전 팁</p>
        </div>
      </div>
    </header>

    <div class="relative flex-1 bg-black flex items-center justify-center">
      <video 
        ref="videoRef" 
        autoplay 
        playsinline 
        muted
        class="absolute inset-0 w-full h-full object-cover opacity-60"
      ></video>

      <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none p-8">
        <div class="w-full max-w-sm h-64 border-2 border-green-500/80 relative flex flex-col items-center justify-center bg-green-500/5 rounded-lg">
          <div class="absolute top-1/3 w-full border-t border-green-400/40 border-dashed"></div>
          <div class="absolute top-2/3 w-full border-t border-green-400/40 border-dashed"></div>
          <div class="absolute left-1/3 h-full border-l border-green-400/40 border-dashed"></div>
          <div class="absolute left-2/3 h-full border-l border-green-400/40 border-dashed"></div>
          
          <span class="bg-black/60 text-white text-xs font-bold px-4 py-1.5 rounded-full backdrop-blur-md mb-2">
            이 영역 안에 서가를 채워주세요
          </span>
          <span class="text-[10px] text-green-300 font-medium">격자선과 책등이 수직이 되도록 유지</span>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-t-3xl p-6 shadow-[0_-10px_40px_rgba(0,0,0,0.3)] z-20 -mt-6 relative">
      <div class="w-12 h-1.5 bg-stone-200 rounded-full mx-auto mb-5"></div>
      
      <h3 class="font-bold text-stone-900 text-[15px] mb-4">✅ 완벽한 인식을 위한 3가지 규칙</h3>
      
      <ul class="flex flex-col gap-4 mb-7">
        <li class="flex items-start gap-3">
          <div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">1</div>
          <p class="text-[13px] text-stone-700 leading-snug">
            <span class="font-bold text-stone-900 block mb-0.5">수평·수직 맞추기</span> 
            스마트폰을 서가와 평행하게 들고, 책등이 찌그러지지 않게 정면에서 촬영하세요.
          </p>
        </li>
        <li class="flex items-start gap-3">
          <div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">2</div>
          <p class="text-[13px] text-stone-700 leading-snug">
            <span class="font-bold text-stone-900 block mb-0.5">권장 수량 (1칸 분량)</span> 
            사진 1장 당 <span class="text-emerald-600 font-bold">110~20권</span> 내외의 책이 들어가게 찍으면 Gemma4의 텍스트 인식(OCR) 성능이 극대화됩니다.
          </p>
        </li>
        <li class="flex items-start gap-3">
          <div class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">3</div>
          <p class="text-[13px] text-stone-700 leading-snug">
            <span class="font-bold text-stone-900 block mb-0.5">책등 코팅 난반사 주의</span> 
            조명이 강하게 반사되어 글자가 안 보이는 부분이 있다면, 촬영 각도를 위아래로 살짝 조절해주세요.
          </p>
        </li>
      </ul>

      <button 
        @click="router.push('/camera')" 
        class="w-full bg-stone-900 hover:bg-stone-800 text-white font-bold py-4 rounded-xl shadow-md active:scale-[0.98] transition-all flex justify-center items-center gap-2 text-sm"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        실제 촬영하러 가기
      </button>
    </div>
  </main>
</template>
