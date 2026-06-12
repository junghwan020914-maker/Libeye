<script setup lang="ts">
import { useRouter } from 'vue-router';
import GuideShotExamples from '../components/guide/GuideShotExamples.vue';
import GuideChecklist from '../components/guide/GuideChecklist.vue';

const router = useRouter();
</script>

<template>
  <main class="flex-col h-full bg-stone-50 relative flex animate-fade-in">
    <header class="bg-white px-4 py-3 border-b border-stone-200 flex items-center shrink-0 sticky top-0 z-20">
      <button @click="router.back()" class="p-2 text-stone-600 text-xl font-bold mr-2 active:scale-90 transition-transform">◀</button>
      <div>
        <h1 class="text-base font-extrabold text-stone-900">촬영 가이드</h1>
        <p class="text-[10px] font-medium text-stone-500">정확도를 90% 이상 올리는 비법</p>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-5 pb-28 flex flex-col gap-6">
      <GuideShotExamples />
      <GuideChecklist />
    </div>

    <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-stone-50 via-stone-50 to-transparent z-20">
      <button 
        @click="router.push('/camera')" 
        class="w-full bg-stone-900 hover:bg-stone-800 text-white font-bold py-4 rounded-xl shadow-[0_4px_14px_0_rgba(0,0,0,0.25)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 text-sm"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        스캔 시작하기
      </button>
    </div>
  </main>
</template>
