<script setup lang="ts">
import { ref } from 'vue';
// 🚨 추가됨: API 호출 함수 임포트
import { searchBooks } from '../../api/sessionAPI';
import BookSearchResultCard from './BookSearchResultCard.vue';

// 🚨 추가됨: 검색 관련 상태 변수
const searchQuery = ref('');
const searchResults = ref<any[]>([]);
const isSearching = ref(false);
const hasSearched = ref(false); // 검색 시도 여부 (결과 없음 표시용)

// 🚨 추가됨: 검색 실행 함수
const performSearch = async () => {
  const query = searchQuery.value.trim();
  if (!query) return;

  isSearching.value = true;
  hasSearched.value = true;
  searchResults.value = []; // 기존 결과 초기화

  try {
    const response = await searchBooks(query);
    searchResults.value = response.results || [];
  } catch (error) {
    console.error('도서 검색 중 오류 발생:', error);
    alert('검색 중 오류가 발생했습니다.');
  } finally {
    isSearching.value = false;
  }
};

// 🚀 추가됨: 검색 초기화 함수
const clearSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  hasSearched.value = false;
};
</script>

<template>
  <section class="flex flex-col gap-3 mt-2">
    <div class="flex items-center justify-between px-1">
      <h3 class="font-bold text-stone-800 text-sm">도서 위치 찾기</h3>
      <span v-if="isSearching" class="text-xs text-stone-500 animate-pulse">검색 중...</span>
    </div>

    <div class="bg-stone-50 border border-stone-200 rounded-2xl p-4 shadow-sm flex flex-col gap-4">

      <div class="relative">
        <input v-model="searchQuery" @keyup.enter="performSearch" type="text" placeholder="도서명 또는 청구기호 검색"
          class="w-full bg-white border border-stone-200 rounded-xl p-3 pl-10 pr-10 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-stone-800 transition-all" />
        <button @click="performSearch"
          class="absolute left-3 top-3 text-stone-400 hover:text-stone-700 transition-colors">
          🔍
        </button>
        <button v-if="searchQuery || hasSearched" @click="clearSearch"
          class="absolute right-3 top-2.5 text-stone-400 hover:text-stone-700 transition-colors w-7 h-7 flex items-center justify-center rounded-full hover:bg-stone-100">
          ✕
        </button>
      </div>

      <div v-if="searchResults.length > 0" class="flex flex-col gap-3">
        <BookSearchResultCard v-for="book in searchResults" :key="book.book_id" :book="book" />
      </div>

      <div v-else-if="hasSearched && !isSearching"
        class="bg-white/60 border border-stone-200/60 rounded-xl p-6 text-center">
        <div class="text-2xl mb-2">📚</div>
        <div class="text-stone-600 text-sm font-medium">검색 결과가 없습니다.</div>
        <div class="text-stone-400 text-xs mt-1">다른 검색어를 입력해 보세요.</div>
      </div>

    </div>
  </section>
</template>
