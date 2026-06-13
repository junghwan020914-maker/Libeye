<script setup lang="ts">
defineProps<{
  editingBook: any;
  searchQuery: string;
  searchResults: any[];
  isSearching: boolean;
  selectedCandidate: any;
}>();
const emit = defineEmits<{
  (e: 'update:searchQuery', value: string): void;
  (e: 'search-input'): void;
  (e: 'select-candidate', book: any): void;
  (e: 'close'): void;
  (e: 'match'): void;
  (e: 'ignore'): void;
  (e: 'zoom', data: any): void;
}>();

// v-model + @input 순서와 동일하게: 값 갱신 emit 후 검색 트리거 emit
const onInput = (e: Event) => {
  emit('update:searchQuery', (e.target as HTMLInputElement).value);
  emit('search-input');
};
</script>

<template>
  <div class="absolute inset-0 bg-stone-900/60 z-50 flex items-end justify-center"
    @click.self="emit('close')">
    <div
      class="bg-white w-full rounded-t-3xl p-6 flex flex-col gap-4 animate-slide-up max-h-[85vh] overflow-y-auto relative">

      <div class="flex justify-between items-center border-b border-stone-100 pb-2">
        <div>
          <h3 class="text-sm font-extrabold text-stone-900">도서 정보 수동 교정</h3>
          <p class="text-[10px] text-stone-400 mt-0.5">Vision AI가 해독하지 못한 청구기호를 수동으로 입력합니다.</p>
        </div>
        <button @click="emit('close')" class="text-stone-400 text-xl p-1">✕</button>
      </div>

      <div
        class="flex flex-col items-center bg-stone-50 p-3 rounded-xl border border-stone-100 shadow-inner gap-2">
        <div class="relative group max-w-[120px]">
          <img v-if="editingBook?.crop_image_url" :src="editingBook.crop_image_url"
            class="h-36 object-contain rounded shadow border border-stone-200 bg-white" />
          <div v-else
            class="h-36 w-20 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-[10px] text-stone-500">
            책등 이미지 없음</div>
        </div>

        <button v-if="editingBook?.crop_image_url" @click="emit('zoom', editingBook)" type="button"
          class="flex items-center gap-1 bg-white text-stone-700 border border-stone-300 px-3 py-1.5 rounded-lg text-[10px] font-bold shadow-sm active:bg-stone-50 transition-colors">
          <span>🔍</span> 이미지 크게 보기
        </button>
      </div>

      <div class="bg-stone-50 p-2.5 rounded-lg text-[10px] text-stone-600 flex flex-col gap-1 font-mono">
        <div>🤖 <strong>AI OCR 결과:</strong> {{ editingBook?.ocr_call_number || '판독 불가' }}</div>
        <div>🎯 <strong>YOLO Segmentation 신뢰도:</strong> {{ editingBook ? Math.round(editingBook.confidence) : 0
          }}%</div>
      </div>

      <div class="flex flex-col gap-3">
        <div class="flex flex-col gap-1"> <label class="text-[11px] font-bold text-stone-500">매칭할 도서명 또는
            청구기호
            검색</label>
          <input type="text" :value="searchQuery" @input="onInput" placeholder="검색어 입력..."
            class="border border-stone-300 rounded-xl p-3 text-xs focus:outline-none focus:border-stone-800" />

          <div v-if="searchQuery && (isSearching || searchResults.length > 0)"
            class="w-full bg-white border border-stone-200 shadow-sm rounded-lg max-h-40 overflow-y-auto mt-1">
            <div v-if="isSearching" class="p-3 text-center text-[10px] text-stone-500">검색 중...</div>
            <div v-else v-for="book in searchResults" :key="book.book_id"
              @click="emit('select-candidate', book)"
              class="p-2 border-b border-stone-100 cursor-pointer hover:bg-stone-50 transition-colors"
              :class="{ 'bg-green-50 border-l-4 border-green-500': selectedCandidate?.book_id === book.book_id }">
              <div class="font-bold text-xs text-stone-800">{{ book.call_number }}</div>
              <div class="text-[10px] text-stone-500 truncate mt-0.5">{{ book.title }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-2 mt-2">
        <button @click="emit('ignore')" type="button"
          class="w-full bg-red-50 text-red-600 hover:text-red-700 border border-red-200 font-bold py-2.5 rounded-xl text-xs transition-colors flex items-center justify-center gap-1 shadow-sm">
          🗑️ 책이 아님 (탐지 결과 삭제)
        </button>

        <div class="flex gap-2">
          <button @click="emit('close')"
            class="flex-1 bg-stone-100 text-stone-700 text-xs font-bold py-3.5 rounded-xl">
            취소
          </button>
          <button @click="emit('match')" :disabled="!selectedCandidate"
            class="flex-[2] text-white text-xs font-bold py-3.5 rounded-xl shadow-md transition-colors"
            :class="selectedCandidate ? 'bg-stone-800 hover:bg-stone-700' : 'bg-stone-300 cursor-not-allowed'">
            선택한 도서로 강제 매칭
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
