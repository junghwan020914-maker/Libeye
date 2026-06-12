<script setup lang="ts">
defineProps<{ isCropping: boolean; isUploading: boolean; isCameraError: boolean }>();
const emit = defineEmits<{
  (e: 'gallery'): void;
  (e: 'shutter'): void;
  (e: 'apply-crop'): void;
  (e: 'cancel-crop'): void;
}>();
</script>

<template>
  <div class="h-32 bg-black flex items-center justify-around px-6 shrink-0 relative z-20">
    <button @click="emit('gallery')" class="w-12 h-12 text-white/80 text-2xl flex items-center justify-center bg-stone-800 rounded-full active:bg-stone-700">
      🖼
    </button>

    <button v-if="!isCropping" @click="emit('shutter')" :disabled="isUploading || isCameraError" class="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center bg-white/20 active:scale-95 transition-all disabled:opacity-50">
      <div class="w-12 h-12 rounded-full bg-white"></div>
    </button>

    <button v-else @click="emit('apply-crop')" :disabled="isUploading" class="px-6 py-3 bg-[#4CAF50] text-white font-bold rounded-full active:scale-95 transition-all disabled:opacity-50 shadow-lg shadow-[#4CAF50]/20">
      크롭 완료
    </button>

    <button v-if="isCropping" @click="emit('cancel-crop')" class="w-12 h-12 text-white/80 text-lg flex items-center justify-center bg-stone-800 rounded-full active:bg-stone-700">
      ✕
    </button>
    <button v-else class="w-12 h-12 text-white/80 text-2xl flex items-center justify-center">
      🔄
    </button>
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
</style>
