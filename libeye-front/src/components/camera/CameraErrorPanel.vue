<script setup lang="ts">
const emit = defineEmits<{ (e: 'simulate'): void }>();
</script>

<template>
  <div class="absolute inset-0 bg-stone-900 z-20 flex flex-col items-center justify-center p-6 text-center">
    <span class="text-4xl mb-4">🚫</span>
    <h3 class="text-white font-bold mb-2">카메라 권한 필요</h3>
    <p class="text-stone-400 text-xs mb-6">데스크톱 등 카메라가 없는 경우<br>테스트 이미지를 업로드하거나 가상 캡처를 사용하세요.</p>
    <button @click="emit('simulate')" class="px-6 py-3 bg-stone-700 text-white rounded-xl font-bold active:bg-stone-600">가상 이미지 캡처</button>
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
