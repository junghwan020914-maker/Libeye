<script setup lang="ts">
defineProps<{ rect: { x: number; y: number; w: number; h: number } }>();
</script>

<template>
  <div class="absolute z-20 border-2 border-[#4CAF50] bg-[#4CAF50]/15 cursor-move"
       :style="{ left: rect.x + 'px', top: rect.y + 'px', width: rect.w + 'px', height: rect.h + 'px' }">
    <div class="w-4 h-4 bg-white border-2 border-[#4CAF50] rounded-full absolute -top-2 -left-2 cursor-nwse-resize z-30"></div>
    <div class="w-4 h-4 bg-white border-2 border-[#4CAF50] rounded-full absolute -top-2 -right-2 cursor-nesw-resize z-30"></div>
    <div class="w-4 h-4 bg-white border-2 border-[#4CAF50] rounded-full absolute -bottom-2 -left-2 cursor-nesw-resize z-30"></div>
    <div class="w-4 h-4 bg-white border-2 border-[#4CAF50] rounded-full absolute -bottom-2 -right-2 cursor-nwse-resize z-30"></div>
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
