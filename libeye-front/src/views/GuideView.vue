<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const baseLux = ref(200);
let animationId: number;

const barWidth = computed(() => Math.min((baseLux.value / 400) * 100, 100) + '%');
const luxColor = computed(() => {
  if (baseLux.value < 80) return '#D32F2F';
  if (baseLux.value > 350) return '#F57C00';
  return '#2E7D32';
});
const luxMessage = computed(() => {
  if (baseLux.value < 80) return '⚠️ 어둡습니다.';
  if (baseLux.value > 350) return '⚠️ 빛 반사 주의.';
  return '💡 적정 조도입니다.';
});

const animateLux = () => {
  baseLux.value += (Math.random() - 0.5) * 30;
  baseLux.value = Math.max(20, Math.min(baseLux.value, 400));
  animationId = requestAnimationFrame(animateLux);
};

onMounted(() => {
  animateLux();
});

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId);
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in z-30 bg-stone-50 relative flex">
    <header class="bg-white px-4 py-3 border-b border-stone-200 flex items-center shrink-0">
      <button @click="router.back()" class="p-2 text-stone-600 text-xl font-bold mr-2">◀</button>
      <div>
        <h1 class="text-base font-extrabold text-stone-900">AI 인식 가이드</h1>
        <p class="text-[10px] font-medium text-stone-500">정확도를 높이는 촬영 팁</p>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
      <div class="bg-white p-4 rounded-2xl shadow-sm border border-stone-200">
        <h3 class="font-bold text-stone-800 text-xs mb-2 flex justify-between">
          <span>현재 조도 상태</span>
          <span :style="{ color: luxColor }">{{ Math.round(baseLux) }} lx</span>
        </h3>
        <div class="h-2.5 bg-stone-200 rounded-full overflow-hidden relative">
          <div class="absolute h-full transition-all duration-300" :style="{ width: barWidth, backgroundColor: luxColor }"></div>
          <div class="absolute left-[30%] h-full w-px bg-white/50"></div>
        </div>
        <p class="text-[9px] text-stone-500 mt-2">{{ luxMessage }}</p>
      </div>

      <div>
        <h3 class="font-bold text-sm text-stone-900 mb-2">올바른 촬영 구도</h3>
        <div class="bg-white border-2 border-[#2E7D32]/50 rounded-xl overflow-hidden mb-3 shadow-sm">
          <div class="h-24 bg-stone-200 relative flex justify-center items-center">
            <div class="absolute top-2 right-2 bg-[#2E7D32] text-white w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs shadow">O</div>
            <span class="text-3xl opacity-50 tracking-tighter">📚📚📚</span>
          </div>
          <div class="p-2.5"><p class="text-[10px] font-bold text-stone-800">✅ 책등이 수직을 이루도록 정면 촬영</p></div>
        </div>
        <div class="bg-white border border-stone-200 rounded-xl overflow-hidden opacity-80 shadow-sm">
          <div class="h-24 bg-stone-200 relative flex justify-center items-center transform -rotate-6 scale-110">
            <div class="absolute top-2 right-2 bg-[#D32F2F] text-white w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs shadow">X</div>
            <span class="text-3xl opacity-50 tracking-tighter filter blur-[1px]">📚📚📚</span>
          </div>
          <div class="p-2.5"><p class="text-[10px] font-bold text-[#D32F2F]">❌ 비스듬한 각도나 흔들림 주의</p></div>
        </div>
      </div>
    </div>
  </main>
</template>
