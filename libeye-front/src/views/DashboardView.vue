<script setup lang="ts">
import { onMounted } from 'vue';
// 1. 신규 북카트 서비스 카드 컴포넌트 임포트
import CartServiceCard from '../components/dashboard/CartServiceCard.vue';
import QuickActionButtons from '../components/dashboard/QuickActionButtons.vue';
import BookSearchPanel from '../components/dashboard/BookSearchPanel.vue';

onMounted(() => {
  // Removed charts for simpler UI
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 flex items-center gap-3 shrink-0">
      <img src="../assets/logo.png" alt="LIBEYE Logo" class="w-8 h-8 object-contain" />
      <h1 class="text-base font-extrabold text-stone-900 tracking-tight">LIBEYE - Library Eye</h1>
    </header>

    <div class="flex-1 overflow-y-auto no-scrollbar p-5 flex flex-col gap-6">

      <QuickActionButtons />

      <BookSearchPanel />

    </div>
  </main>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
