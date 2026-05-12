<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import Chart from 'chart.js/auto';

const router = useRouter();
const progressCanvas = ref<HTMLCanvasElement | null>(null);
const issueCanvas = ref<HTMLCanvasElement | null>(null);

onMounted(() => {
  if (progressCanvas.value) {
    new Chart(progressCanvas.value, {
      type: 'doughnut',
      data: { labels: ['완료','미완료'], datasets: [{ data: [72,28], backgroundColor: ['#292524','#e7e5e4'], borderWidth: 0, cutout: '80%' }] },
      options: { responsive: true, maintainAspectRatio: false, circumference: 180, rotation: 270, plugins: { legend: {display:false}, tooltip: {enabled:false} } }
    });
  }
  
  if (issueCanvas.value) {
    new Chart(issueCanvas.value, {
      type: 'bar',
      data: { labels: ['오배열','누락','초과'], datasets: [{ data: [8,3,1], backgroundColor: ['#D32F2F','#1976D2','#F57C00'], borderRadius: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: {display:false} }, scales: { y: {display: false}, x: {grid: {display: false}, border: {display:false}, ticks: {font: {size: 10}}} } }
    });
  }
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 flex justify-between items-center shrink-0">
      <div>
        <h2 class="text-lg font-extrabold text-stone-900">김사서님, 환영합니다 👋</h2>
        <p class="text-xs font-medium text-stone-500 mt-0.5">오늘 할당된 구역: 인문과학실 A열</p>
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

      <!-- 요약 위젯 -->
      <div class="flex flex-col gap-4">
        <div class="bg-white p-5 rounded-2xl border border-stone-100 shadow-sm flex flex-col relative overflow-hidden">
          <h3 class="font-bold text-stone-800 text-sm mb-1">금일 점검 진척도</h3>
          <div class="relative w-full h-[180px] max-h-[250px] mx-auto -mb-4">
            <canvas ref="progressCanvas"></canvas>
          </div>
          <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex flex-col items-center">
            <span class="text-2xl font-extrabold text-stone-900">72%</span>
          </div>
        </div>
        
        <div class="bg-white p-5 rounded-2xl border border-stone-100 shadow-sm flex flex-col">
          <div class="flex justify-between items-center mb-2">
            <h3 class="font-bold text-stone-800 text-sm">최근 발견된 오류</h3>
            <span class="text-[10px] font-bold px-2 py-0.5 bg-red-50 text-red-600 rounded">조치필요 12</span>
          </div>
          <div class="relative w-full h-[180px] max-h-[250px] mx-auto">
            <canvas ref="issueCanvas"></canvas>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
