<script setup lang="ts">
defineProps<{ image: any }>();
const emit = defineEmits<{ (e: 'close'): void }>();
</script>

<template>
  <div
    class="absolute inset-0 bg-stone-950/95 z-[60] flex flex-col items-center justify-center p-4 animate-fade-in"
    @click="emit('close')">

    <div class="absolute top-6 right-6 flex items-center gap-4 z-10">
      <span
        class="text-white/60 text-xs font-medium bg-black/40 px-3 py-1.5 rounded-full backdrop-blur-sm">화면
        터치
        시 닫힘</span>
      <button @click="emit('close')"
        class="bg-white/10 hover:bg-white/20 text-white w-10 h-10 rounded-full flex items-center justify-center text-xl backdrop-blur-sm transition-colors">✕</button>
    </div>

    <div class="w-full max-w-md max-h-[75vh] flex items-center justify-center overflow-hidden p-2">
      <img :src="image?.crop_image_url"
        class="max-w-full max-h-[72vh] object-contain rounded-lg shadow-2xl border border-white/10 animate-scale-up"
        @click.stop />
    </div>

    <div class="mt-4 bg-black/60 backdrop-blur-md text-white border border-white/10 px-5 py-3 rounded-2xl max-w-xs text-center shadow-lg"
      @click.stop>
      <div class="text-[10px] text-white/50 font-bold uppercase tracking-wider mb-0.5">AI 인식 텍스트</div>
      <div class="text-xs font-mono font-bold text-orange-400 truncate">
        {{ image?.ocr_call_number || image?.call_number || '판독 불가' }}
      </div>
    </div>
  </div>
</template>
