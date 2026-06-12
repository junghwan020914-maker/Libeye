<script setup lang="ts">
const emit = defineEmits<{
  (e: 'go-list'): void;
  (e: 'verify-all'): void;
}>();
</script>

<template>
  <div class="absolute bottom-0 w-full bg-white border-t border-stone-200 p-3 flex gap-2">
    <button @click="emit('go-list')"
      class="flex-1 bg-stone-100 text-stone-700 hover:bg-stone-200 text-xs font-bold py-3 rounded-xl transition-colors">
      목록으로
    </button>
    <button @click="emit('verify-all')"
      class="flex-[2] bg-[#2E7D32] hover:bg-green-700 text-white text-xs font-bold py-3 rounded-xl transition-colors shadow-md">
      일괄 조치 완료 처리
    </button>
  </div>
</template>
