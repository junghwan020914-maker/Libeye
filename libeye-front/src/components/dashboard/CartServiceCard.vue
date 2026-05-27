<template>
  <div class="bg-white p-6 rounded-xl shadow-md border border-gray-100 flex flex-col justify-between transition hover:shadow-lg">
    <div>
      <div class="flex items-center space-x-3 mb-3">
        <div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
          </svg>
        </div>
        <h3 class="text-lg font-bold text-gray-800">북카트 정리 도우미</h3>
      </div>
      <p class="text-sm text-gray-500 mb-6 leading-relaxed">
        반납 도서나 카트 안의 책등을 한 번에 촬영하여 서가별 최적의 배치 순서와 반납 동선을 생성합니다.
      </p>
    </div>
    
    <button
      @click="navigateToCartScan"
      class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition text-center shadow-sm flex items-center justify-center space-x-2"
    >
      <span>북카트 정리 시작</span>
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();

const navigateToCartScan = () => {
  router.push('/cart-scan');
};
</script>
