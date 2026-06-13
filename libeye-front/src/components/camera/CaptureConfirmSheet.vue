<script setup lang="ts">
defineProps<{ previews: string[]; count: number; isUploading: boolean }>();
const emit = defineEmits<{
  (e: 'remove', index: number): void;
  (e: 'take-another'): void;
  (e: 'upload-all'): void;
}>();
</script>

<template>
  <div class="absolute inset-0 bg-stone-900 z-[60] flex flex-col items-center justify-center p-6">
    <h2 class="text-white text-2xl font-bold mb-2">서가 촬영 확인</h2>
    <p class="text-stone-400 mb-6 text-sm">왼쪽부터 순서대로 나열되어 있는지 확인해주세요.</p>

    <div class="flex gap-4 overflow-x-auto w-full pb-4 mb-8 snap-x scrollbar-hide">
      <div v-for="(url, idx) in previews" :key="idx" class="relative min-w-[140px] h-[200px] snap-center shrink-0">
        <img :src="url" class="w-full h-full object-cover rounded-xl border-2 border-stone-600" />
        <div class="absolute top-0 left-0 bg-black/80 text-white text-xs font-bold px-3 py-1.5 rounded-br-xl rounded-tl-xl">
          {{ idx + 1 }}
        </div>
        <button @click="emit('remove', idx)" class="absolute top-2 right-2 bg-red-500/90 hover:bg-red-500 rounded-full w-8 h-8 text-white font-bold flex items-center justify-center shadow-md active:scale-90 transition-transform">
          ✕
        </button>
      </div>
    </div>

    <div class="flex flex-col gap-4 w-full max-w-sm mt-auto pb-10">
      <button @click="emit('take-another')" class="w-full py-4 bg-stone-800 text-white border border-stone-600 rounded-2xl font-bold text-lg active:bg-stone-700 transition-colors">
        ➕ 추가 촬영
      </button>

      <button @click="emit('upload-all')" :disabled="isUploading" class="w-full py-5 bg-[#4CAF50] text-white rounded-2xl font-black text-xl active:scale-95 transition-all shadow-[0_0_20px_rgba(76,175,80,0.3)] disabled:opacity-50">
        <span v-if="!isUploading">🚀 총 {{ count }}장 분석 시작</span>
        <span v-else>⏳ 업로드 중...</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 💡 화면이 파랗게 반전되는 드래그 부작용 방지용 스타일 추가 */
main, img, div {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -webkit-user-drag: none;
}
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
