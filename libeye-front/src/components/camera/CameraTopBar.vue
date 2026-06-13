<script setup lang="ts">
import { useRouter } from 'vue-router';

defineProps<{ selectedLocation: any; isCropping: boolean }>();

const router = useRouter();
</script>

<template>
  <div class="absolute top-0 w-full z-20 p-4 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent pb-10 text-white">
    <button @click="router.push('/')" class="text-2xl px-2">◀</button>
    
    <div class="text-center" v-if="selectedLocation">
      <h1 class="text-sm font-bold">{{ selectedLocation }}</h1>
      <p v-if="!isCropping" class="text-[10px] text-white/70">가이드라인에 맞춰 서가를 촬영해주세요</p>
      <p v-else class="text-[10px] text-white/70">드래그하여 크롭 조절 및 중앙 터치로 상자 이동이 가능합니다</p>
    </div>
    
    <div class="w-10"></div>
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