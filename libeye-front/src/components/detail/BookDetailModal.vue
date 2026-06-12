<script setup lang="ts">
defineProps<{ book: any }>();
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'verify'): void;
  (e: 'edit'): void;
  (e: 'ignore'): void;
  (e: 'zoom', data: any): void;
}>();
</script>

<template>
  <div class="absolute inset-0 bg-stone-900/60 z-50 flex items-center justify-center p-4">
    <div
      class="bg-white w-full max-w-sm rounded-2xl p-6 flex flex-col animate-slide-up shadow-2xl border border-stone-200">

      <div class="flex justify-between items-start mb-3 border-b border-stone-100 pb-3">
        <div>
          <h2 class="text-base font-extrabold text-stone-900 flex items-center gap-2">
            <span>도서 상세 정보</span>
            <span v-if="book.status === 'MATCH'"
              class="text-[10px] font-bold bg-green-100 text-green-700 px-2 py-0.5 rounded-full">정상
              배치</span>
            <span
              v-else-if="book.status === 'MISPLACED' && book._raw_detection?.is_verified"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full"
              :class="book._raw_detection?.verification_method === 'BATCH_OVERWRITE' ? 'bg-stone-200 text-stone-700' : 'bg-green-100 text-green-700'">
              {{ book._raw_detection?.verification_method === 'BATCH_OVERWRITE' ?
              '일괄-강제완료' :
              '제자리-조치완료' }}
            </span>
            <span v-else-if="book.status === 'MISPLACED'"
              class="text-[10px] font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">순서
              오류</span>
            <span v-else-if="book.status === 'EXTRA'"
              class="text-[10px] font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">타
              구역
              도서</span>
          </h2>
        </div>
        <button @click="emit('close')"
          class="text-stone-400 text-2xl leading-none hover:text-stone-600 transition-colors">✕</button>
      </div>

      <div
        class="flex flex-col items-center bg-stone-50 py-3 rounded-xl mb-4 border border-stone-100 shadow-inner gap-2">
        <img v-if="book.crop_image_url" :src="book.crop_image_url"
          class="h-40 object-contain rounded shadow border border-stone-200 bg-white" />
        <div v-else
          class="h-40 w-24 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-xs text-stone-500">
          크롭 사진 없음</div>

        <button v-if="book.crop_image_url"
          @click="emit('zoom', book._raw_detection || book)" type="button"
          class="flex items-center gap-1 bg-white text-stone-700 border border-stone-300 px-2.5 py-1.5 rounded-md text-[10px] font-bold shadow-sm active:bg-stone-50 transition-colors">
          <span>🔍</span> 이미지 크게 보기
        </button>
      </div>

      <div class="flex flex-col gap-2 bg-stone-50 p-3.5 rounded-xl text-xs text-stone-700 mb-4">
        <div class="flex flex-col gap-0.5">
          <span class="text-[10px] font-bold text-stone-400">DB 장서 도서명</span>
          <span class="font-bold text-stone-900 break-all line-clamp-1">{{ book.title
          }}</span>
        </div>
        <div class="border-t border-stone-200/60 my-0.5"></div>

        <div class="grid grid-cols-2 gap-2">
          <div class="flex flex-col gap-0.5">
            <span class="text-[10px] font-bold text-stone-400">청구기호</span>
            <span class="font-semibold text-stone-800 font-mono">{{ book.call_number
            }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-[10px] font-bold text-stone-400">배정 서가 위치</span>
            <span class="font-semibold text-stone-800">{{ book.location }}</span>
          </div>
        </div>
        <div class="border-t border-stone-200/60 my-0.5"></div>

        <div class="grid grid-cols-2 gap-2">
          <div class="flex flex-col gap-0.5">
            <span class="text-[10px] font-bold text-stone-400">서가 정위치 순서(Full 상태에서)</span>
            <span class="font-extrabold text-green-600">{{ book.expected_order }}번째</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-[10px] font-bold text-stone-400">현재 탐지된 순서</span>
            <span class="font-extrabold"
              :class="(book.status === 'MISPLACED' && !book._raw_detection?.is_verified) ? 'text-red-500' : 'text-stone-600'">{{
                book.detected_order }}번째</span>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <button v-if="book.status === 'MISPLACED' && !book._raw_detection?.is_verified"
          @click="emit('verify')" type="button"
          class="w-full bg-[#2E7D32] text-white font-bold py-3 rounded-xl text-xs hover:bg-green-700 transition-colors shadow-md flex justify-center items-center gap-1">
          ✓ 오배열 물리적 조치 완료
        </button>

        <button @click="emit('edit')" type="button"
          class="w-full bg-stone-100 text-stone-600 hover:text-stone-900 border border-stone-300 font-bold py-2 rounded-xl text-[11px] transition-colors flex items-center justify-center gap-1">
          ✏️ 인식을 잘못했나요? 수동 교정하기
        </button>

        <button @click="emit('ignore')" type="button"
          class="w-full bg-red-50 text-red-600 hover:text-red-700 border border-red-200 font-bold py-2 rounded-xl text-[11px] transition-colors flex items-center justify-center gap-1">
          🗑️ 책이 아님 (탐지 결과 삭제)
        </button>

        <button @click="emit('close')"
          class="w-full bg-stone-800 text-white font-bold py-3 rounded-xl text-xs hover:bg-stone-700 transition-colors shadow-md">
          {{ book.status === 'MISPLACED' && !book._raw_detection?.is_verified ? '다음에 하기 (닫기)' : '닫기' }}
        </button>
      </div>

    </div>
  </div>
</template>
