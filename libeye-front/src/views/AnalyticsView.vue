<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Chart from 'chart.js/auto';
import { getAnalytics } from '../api/sessionAPI';

const weeklyCanvas = ref<HTMLCanvasElement | null>(null);
const typeCanvas = ref<HTMLCanvasElement | null>(null);
const aiCanvas = ref<HTMLCanvasElement | null>(null);
const aiSuccessRate = ref(0);

onMounted(async () => {
  try {
    const data = await getAnalytics();
    
    if (weeklyCanvas.value) {
      new Chart(weeklyCanvas.value, {
        type: 'bar',
        data: { labels: ['월','화','수','목','금','토'], datasets: [{ data: data.weekly_scans, backgroundColor: '#292524', borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: {display:false} }, scales: { y: {display: false}, x: {grid: {display: false}, border: {display:false}} } }
      });
    }

    if (typeCanvas.value) {
      const errorData = [
        data.error_ratios.MISPLACED || 0,
        data.error_ratios.UNKNOWN || 0,
      ];
      new Chart(typeCanvas.value, {
        type: 'doughnut',
        data: { labels: ['오배열', '인식실패'], datasets: [{ data: errorData, backgroundColor: ['#D32F2F', '#F57C00'], borderWidth: 0, cutout: '60%' }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: {position: 'bottom', labels: {boxWidth: 8, font:{size: 9}}} } }
      });
    }

    if (aiCanvas.value) {
      aiSuccessRate.value = data.ai_success_rate;
      new Chart(aiCanvas.value, {
        type: 'doughnut',
        data: { labels: ['성공','수동'], datasets: [{ data: [data.ai_success_rate, 100 - data.ai_success_rate], backgroundColor: ['#2E7D32','#e7e5e4'], borderWidth: 0, cutout: '75%', circumference: 180, rotation: 270 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: {display:false}, tooltip: {enabled:false} } }
      });
    }
  } catch(e) {
    console.error(e);
  }
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 bg-stone-50 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <h1 class="text-xl font-extrabold text-stone-900">서고 관리 인사이트</h1>
      <p class="text-xs font-medium text-stone-500">2026년 4월 4주차 리포트</p>
    </header>

    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
      <div class="bg-white p-4 rounded-2xl shadow-sm border border-stone-200">
        <h3 class="font-bold text-stone-800 text-sm mb-2">주간 서가 점검량 (칸 단위)</h3>
        <div class="relative w-full h-[180px] max-h-[250px] mx-auto">
          <canvas ref="weeklyCanvas"></canvas>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="bg-white p-4 rounded-2xl shadow-sm border border-stone-200 flex flex-col items-center">
          <h3 class="font-bold text-stone-800 text-xs w-full text-left">발견된 오류 비율</h3>
          <div class="relative w-full h-[140px] max-h-[200px] mx-auto mt-2">
            <canvas ref="typeCanvas"></canvas>
          </div>
        </div>
        <div class="bg-white p-4 rounded-2xl shadow-sm border border-stone-200 flex flex-col items-center relative">
          <h3 class="font-bold text-stone-800 text-xs w-full text-left">AI 인식 성공률</h3>
          <div class="relative w-full h-[140px] max-h-[200px] mx-auto mt-4">
            <canvas ref="aiCanvas"></canvas>
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 mt-1">
              <span class="text-xl font-extrabold">{{ aiSuccessRate }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
