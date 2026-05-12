<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 bg-stone-50 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <h1 class="text-xl font-extrabold text-stone-900">스캔 히스토리</h1>
      <div class="flex gap-2 mt-4 overflow-x-auto no-scrollbar pb-1">
        <button class="px-4 py-1.5 rounded-full bg-stone-800 text-white text-[11px] font-bold">전체보기</button>
        <button class="px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold">조치 필요 ⚠️</button>
        <button class="px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold">완료 ✅</button>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-stone-100/50">
      <!-- Dummy items based on UI_Aggregated_2 -->
      <div @click="router.push('/detail')" class="bg-white rounded-xl shadow-sm border border-stone-200 border-l-4 border-l-red-500 p-4 flex items-center justify-between cursor-pointer active:scale-[0.98]">
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <h3 class="font-extrabold text-stone-900 text-sm">인문과학실 A-2-3</h3>
            <span class="text-[9px] font-bold bg-red-100 text-red-700 px-1 rounded">미결</span>
          </div>
          <p class="text-[10px] font-medium text-stone-500">오늘 14:15 · 총 25권 스캔</p>
          <div class="flex gap-1 mt-1">
            <span class="px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-[9px] font-bold">⚠ 오배열 1</span>
            <span class="px-1.5 py-0.5 bg-orange-50 text-orange-700 border border-orange-200 rounded text-[9px] font-bold">🔍 인식불가 1</span>
          </div>
        </div>
        <div class="text-stone-300 text-xl font-bold">❯</div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-stone-200 p-4 flex items-center justify-between opacity-80">
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <h3 class="font-extrabold text-stone-900 text-sm">인문과학실 A-2-2</h3>
            <span class="text-[9px] font-bold bg-green-100 text-green-700 px-1 rounded">완료</span>
          </div>
          <p class="text-[10px] font-medium text-stone-500">오늘 14:02 · 총 30권 스캔</p>
          <div class="flex gap-1 mt-1">
            <span class="px-1.5 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded text-[9px] font-bold">✅ 전체 정상</span>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
