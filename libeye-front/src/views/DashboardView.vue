<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import Chart from 'chart.js/auto';

const router = useRouter();
const progressCanvas = ref<HTMLCanvasElement | null>(null);
const issueCanvas = ref<HTMLCanvasElement | null>(null);

onMounted(() => {
  // Removed charts for simpler UI
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 flex justify-between items-center shrink-0">
      <div>
        <h2 class="text-lg font-extrabold text-stone-900">김사서님, 환영합니다 👋</h2>
      </div>
      <div class="w-10 h-10 rounded-full bg-stone-800 flex items-center justify-center text-white font-bold shadow-sm">김</div>
    </header>

    <div class="flex-1 overflow-y-auto no-scrollbar p-5 flex flex-col gap-6">
      <!-- 퀵 액션 (스캔 & 가이드) -->
      <div class="flex gap-3">
        <button @click="router.push('/camera')" class="flex-[2] bg-stone-800 text-white p-4 rounded-2xl shadow-lg flex flex-col items-start justify-center gap-1 active:scale-[0.98] transition-transform overflow-hidden relative">
          <div class="absolute -right-4 -top-4 text-6xl opacity-20">📸</div>
          <span class="font-bold text-lg relative z-10">새 서가 점검</span>
          <span class="text-[10px] text-white/70 relative z-10">터치하여 카메라 실행</span>
        </button>
        <button @click="router.push('/guide')" class="flex-1 bg-white border border-stone-200 text-stone-800 p-4 rounded-2xl shadow-sm flex flex-col items-center justify-center gap-1 active:scale-[0.98] transition-transform">
          <span class="text-2xl">💡</span>
          <span class="font-bold text-xs mt-1">촬영 가이드</span>
        </button>
      </div>

      <!-- 요약 위젯 삭제됨 -->
    </div>
  </main>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
