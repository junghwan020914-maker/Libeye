<template>
  <div class="absolute inset-0 bg-stone-900/90 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
    <div class="w-16 h-16 border-4 border-stone-600 border-t-green-500 rounded-full animate-spin mb-6"></div>
    <h2 class="text-white font-extrabold text-lg tracking-wide animate-pulse">Vision AI 분석 중...</h2>
    <p class="text-stone-400 text-xs mt-2">청구기호 해독 및 배가 상태 비교</p>
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
