<template>
  <div class="absolute border-2 border-white/50 flex flex-col justify-evenly items-center pointer-events-none z-10" style="left: 5%; right: 5%; top: 20%; bottom: 20%; box-shadow: 0 0 0 9999px rgba(0,0,0,0.6);">
    <div class="w-full h-px bg-white/30 absolute top-1/3"></div>
    <div class="w-full h-px bg-white/30 absolute top-2/3"></div>
    <div class="absolute w-px h-full bg-white/30"></div>
    <div class="w-6 h-6 border-l-4 border-t-4 border-[#4CAF50] absolute top-[-2px] left-[-2px]"></div>
    <div class="w-6 h-6 border-r-4 border-t-4 border-[#4CAF50] absolute top-[-2px] right-[-2px]"></div>
    <div class="w-6 h-6 border-l-4 border-b-4 border-[#4CAF50] absolute bottom-[-2px] left-[-2px]"></div>
    <div class="w-6 h-6 border-r-4 border-b-4 border-[#4CAF50] absolute bottom-[-2px] right-[-2px]"></div>
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
