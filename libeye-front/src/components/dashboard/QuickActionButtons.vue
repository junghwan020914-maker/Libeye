<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex gap-3">
      <button @click="router.push('/camera')"
        class="flex-[2] bg-stone-800 text-white p-4 rounded-2xl shadow-lg flex flex-col items-start justify-center gap-1 active:scale-[0.98] transition-transform overflow-hidden relative">
        <div class="absolute -right-4 -top-4 text-6xl opacity-20">📸</div>
        <span class="font-bold text-lg relative z-10">새 서가 점검</span>
        <span class="text-[10px] text-white/70 relative z-10">터치하여 카메라 실행</span>
      </button>
      <button @click="router.push('/guide')"
        class="flex-1 bg-white border border-stone-200 text-stone-800 p-4 rounded-2xl shadow-sm flex flex-col items-center justify-center gap-1 active:scale-[0.98] transition-transform">
        <span class="text-2xl">💡</span>
        <span class="font-bold text-xs mt-1">촬영 가이드</span>
      </button>
    </div>

    
  </div>
</template>
