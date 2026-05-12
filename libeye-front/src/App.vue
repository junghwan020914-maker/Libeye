<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

// hide GNB on specific routes
const hideNavRoutes = ['login', 'camera', 'detail', 'guide'];
const showNav = computed(() => {
  return route.name && !hideNavRoutes.includes(route.name as string);
});
</script>

<template>
  <!-- Router View takes up the remaining space -->
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <!-- Global Navigation Bar -->
  <nav v-if="showNav" class="absolute bottom-0 w-full bg-white border-t border-stone-200 px-4 py-2 pb-safe flex justify-between shrink-0 z-40 pb-4">
    <button @click="router.push('/')" class="flex-1 flex flex-col items-center gap-1 p-1 active:scale-90 transition-transform" :class="route.name === 'dashboard' ? 'text-stone-900 font-bold' : 'text-stone-400 font-normal'">
      <span class="text-xl h-6 flex items-center">🏠</span><span class="text-[9px]">홈</span>
    </button>
    <button @click="router.push('/history')" class="flex-1 flex flex-col items-center gap-1 p-1 active:scale-90 transition-transform" :class="route.name === 'history' ? 'text-stone-900 font-bold' : 'text-stone-400 font-normal'">
      <span class="text-xl h-6 flex items-center">📋</span><span class="text-[9px]">목록</span>
    </button>
    <button @click="router.push('/camera')" class="flex-1 flex flex-col items-center gap-1 p-1 text-stone-400 font-normal active:scale-90 transition-transform relative">
      <div class="absolute -top-4 w-10 h-10 bg-stone-800 rounded-full flex items-center justify-center shadow-lg border-2 border-white"><span class="text-white text-lg">📸</span></div>
      <span class="text-[9px] font-bold mt-5">스캔</span>
    </button>
    <button @click="router.push('/map')" class="flex-1 flex flex-col items-center gap-1 p-1 active:scale-90 transition-transform" :class="route.name === 'map' ? 'text-stone-900 font-bold' : 'text-stone-400 font-normal'">
      <span class="text-xl h-6 flex items-center">🗺️</span><span class="text-[9px]">지도</span>
    </button>
    <button @click="router.push('/analytics')" class="flex-1 flex flex-col items-center gap-1 p-1 active:scale-90 transition-transform" :class="route.name === 'analytics' ? 'text-stone-900 font-bold' : 'text-stone-400 font-normal'">
      <span class="text-xl h-6 flex items-center">📊</span><span class="text-[9px]">통계</span>
    </button>
  </nav>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
