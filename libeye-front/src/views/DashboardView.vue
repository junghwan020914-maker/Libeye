<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
// 🚨 추가됨: API 호출 함수 임포트
import { searchBooks } from '../api/sessionAPI';
// 1. 신규 북카트 서비스 카드 컴포넌트 임포트
import CartServiceCard from '../components/dashboard/CartServiceCard.vue';

const router = useRouter();

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

      <div class="flex flex-col gap-3">
        <div class="flex gap-3">
          <button @click="router.push('/camera')"
            class="flex-[2] bg-stone-800 text-white p-4 rounded-2xl shadow-lg flex flex-col items-start justify-center gap-1 active:scale-[0.98] transition-transform overflow-hidden relative">
            <div class="absolute -right-4 -top-4 text-6xl opacity-20">📸</div>
            <span class="font-bold text-lg relative z-10">새 서가 점검</span>
            <span class="text-[10px] text-white/70 relative z-10">터치하여 카메라 실행</span>
          </button>
          <button @click="router.push('/guide')"
            class="flex-1 bg-white border border-stone-200 text-stone-800 p-4 rounded-2xl shadow-sm flex flex-col items-center justify-center gap-1 active:scale-[0.98] transition-transform">
            <span class="text-2xl">💡</span>
            <span class="font-bold text-xs mt-1">촬영 가이드</span>
          </button>
        </div>

        <button @click="router.push('/cart-scan')"
          class="w-full bg-blue-50 border border-blue-100 p-4 rounded-2xl shadow-sm flex items-center justify-between active:scale-[0.98] transition-transform">
          <div class="flex items-center gap-3">
            <div
              class="text-2xl bg-white text-blue-600 w-10 h-10 flex items-center justify-center rounded-xl shadow-sm">🛒
            </div>
            <div class="text-left">
              <div class="font-bold text-blue-900 text-sm">북카트 정리 도우미</div>
              <div class="text-xs text-blue-700 mt-0.5">도서 배치 최적 동선 안내</div>
            </div>
          </div>
          <div class="text-blue-500 font-bold">➔</div>
        </button>
      </div>

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
            <div v-for="book in searchResults" :key="book.book_id"
              class="bg-white rounded-xl border border-stone-200/80 shadow-sm flex flex-col overflow-hidden transition-all duration-200 hover:shadow-md hover:border-stone-300 relative"
              :class="[
                !book.last_seen_location ? 'border-l-4 border-l-stone-300' :
                  (book.assigned_location !== book.last_seen_location ? 'border-l-4 border-l-red-500' : 'border-l-4 border-l-emerald-500')
              ]">
              
              <div class="p-3.5 pb-2.5 flex flex-col gap-2">
                <div class="flex items-start justify-between gap-3">
                  <span class="font-bold text-stone-900 text-sm leading-snug break-keep flex-1">
                    {{ book.title }}
                  </span>
                  <span v-if="book.last_seen_location && book.assigned_location !== book.last_seen_location" 
                    class="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-md border border-red-100 shrink-0">
                    위치 다름
                  </span>
                  <span v-else-if="book.last_seen_location" 
                    class="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100 shrink-0">
                    정상 위치
                  </span>
                </div>
                
                <div class="inline-flex items-center self-start bg-stone-100 text-stone-600 text-[11px] px-2 py-0.5 rounded-md border border-stone-200/60 font-medium">
                  📋 {{ book.call_number }}
                </div>
              </div>

              <div class="px-3.5 py-2.5 bg-stone-50/60 border-t border-stone-100 flex flex-col gap-2 text-xs">
                <div class="grid grid-cols-2 gap-2">
                  <div class="flex flex-col gap-1">
                    <span class="text-stone-400 text-[10px] font-medium">원래 위치</span>
                    <span class="font-semibold text-stone-700 bg-white border border-stone-200/60 px-2 py-1 rounded-lg inline-block truncate text-center">
                      {{ book.assigned_location || '미지정' }}
                    </span>
                  </div>
                  <div class="flex flex-col gap-1">
                    <span class="text-stone-400 text-[10px] font-medium">최근 발견 위치</span>
                    <span class="font-semibold px-2 py-1 rounded-lg inline-block truncate text-center border" :class="[
                      !book.last_seen_location ? 'text-stone-400 bg-white border-stone-200/60' :
                        (book.assigned_location !== book.last_seen_location ? 'text-red-600 bg-red-50/80 border-red-200' : 'text-emerald-600 bg-emerald-50/80 border-emerald-200')
                    ]">
                      {{ book.last_seen_location || '스캔 없음' }}
                    </span>
                  </div>
                </div>

                <div v-if="book.last_seen_location && book.last_seen_time" 
                  class="flex items-center justify-between text-[10px] text-stone-400 pt-1.5 border-t border-stone-200/50 px-0.5">
                  <span class="flex items-center gap-1">
                    <span>⏱️ 최근 발견 시간</span>
                  </span>
                  <span class="font-medium text-stone-500">{{ book.last_seen_time }}</span>
                </div>
              </div>

            </div>
          </div>

          <div v-else-if="hasSearched && !isSearching"
            class="bg-white/60 border border-stone-200/60 rounded-xl p-6 text-center">
            <div class="text-2xl mb-2">📚</div>
            <div class="text-stone-600 text-sm font-medium">검색 결과가 없습니다.</div>
            <div class="text-stone-400 text-xs mt-1">다른 검색어를 입력해 보세요.</div>
          </div>

        </div>
      </section>

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
