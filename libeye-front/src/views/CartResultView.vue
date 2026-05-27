<template>
  <div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">도서 정리 추천 동선</h1>
    
    <div v-if="status === 'PENDING' || status === 'PROCESSING'" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-lg font-semibold text-gray-700">AI가 서가 위치를 분석 중입니다...</p>
    </div>

    <div v-else-if="error" class="text-center text-red-600 py-10">
      <p>{{ error }}</p>
      <button @click="$router.push('/cart-scan')" class="mt-4 text-blue-500 underline">다시 시도하기</button>
    </div>

    <div v-else-if="resultData" class="space-y-4">
      <p class="text-gray-600 mb-4">아래 순서대로 카트를 이동하며 책을 꽂아주세요.</p>
      
      <div 
        v-for="(book, index) in resultData.books" 
        :key="book.id"
        class="flex items-center bg-white p-4 rounded-lg shadow border-l-4 border-blue-500"
      >
        <div class="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold mr-4">
          {{ index + 1 }}
        </div>
        <div class="flex-grow">
          <h3 class="font-bold text-gray-800">{{ book.title }}</h3>
          <p class="text-sm text-gray-500">청구기호: {{ book.call_number }}</p>
        </div>
        <div class="text-right">
          <span class="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
            {{ book.shelf_location || '위치 미상' }}
          </span>
        </div>
      </div>
      
      <div class="mt-8 text-center">
        <button @click="$router.push('/cart-scan')" class="bg-gray-800 text-white px-6 py-2 rounded shadow">
          새로운 카트 스캔
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useCartPolling } from '../composables/useCartPolling';

const route = useRoute();
const sessionId = Number(route.params.id);

const { status, resultData, error, startPolling } = useCartPolling();

onMounted(() => {
  if (sessionId) {
    startPolling(sessionId);
  }
});
</script>