<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const isLoading = ref(false);

const handleLogin = () => {
  isLoading.value = true;
  setTimeout(() => {
    router.push('/');
  }, 800);
};
</script>

<template>
  <main class="w-full h-full flex flex-col items-center justify-center p-6 relative z-10 bg-stone-50 animate-fade-in">
    <div class="bg-white p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] w-full border border-stone-100 flex flex-col gap-8">
      <div class="text-center mt-4">
        <div class="text-5xl mb-4">📚</div>
        <h1 class="text-2xl font-extrabold text-stone-900 tracking-tight">스마트 서고 관리</h1>
        <p class="text-stone-500 text-sm mt-2 font-medium">Vision AI & Gemma4 기반 배가 점검</p>
      </div>
      <form @submit.prevent="handleLogin" class="flex flex-col gap-4">
        <div>
          <label class="block text-xs font-bold text-stone-600 mb-1 ml-1">사번 (아이디)</label>
          <input type="text" value="LIB-2026" class="w-full px-4 py-3 rounded-xl bg-stone-50 border border-stone-200 focus:outline-none focus:ring-2 focus:ring-stone-800 text-stone-900 font-medium">
        </div>
        <div>
          <label class="block text-xs font-bold text-stone-600 mb-1 ml-1">비밀번호</label>
          <input type="password" value="password" class="w-full px-4 py-3 rounded-xl bg-stone-50 border border-stone-200 focus:outline-none focus:ring-2 focus:ring-stone-800 text-stone-900 font-medium">
        </div>
        <button type="submit" class="mt-4 w-full bg-stone-800 hover:bg-stone-900 text-white font-bold py-4 rounded-xl shadow-md transition-all active:scale-[0.98] flex justify-center items-center gap-2">
          <span v-if="!isLoading">로그인</span>
          <div v-else class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
        </button>
      </form>
    </div>
  </main>
</template>
