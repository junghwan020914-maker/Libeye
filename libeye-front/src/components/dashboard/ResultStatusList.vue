<script setup lang="ts">
import { computed } from 'vue';
import type { DetectionResult } from '../../types/session';

const props = defineProps<{
  detections: DetectionResult[];
}>();

// 상태별로 도서 분류 (순서대로 정렬 추가)
const matchedBooks = computed(() => props.detections.filter(d => d.status === 'MATCH').sort((a,b) => a.detected_order - b.detected_order));
const misplacedBooks = computed(() => props.detections.filter(d => d.status === 'MISPLACED').sort((a,b) => a.detected_order - b.detected_order));
// 변경 후 (💡 OCR_FAILED와 MATCH_FAILED 조건 추가)
const unknownBooks = computed(() => 
  props.detections
    .filter(d => 
      d.status === 'UNKNOWN' || 
      d.status === 'MISSING' || 
      d.status === 'OCR_FAILED' || 
      d.status === 'MATCH_FAILED'
    )
    .sort((a, b) => a.detected_order - b.detected_order)
);

</script>

<template>
  <div class="mt-6 w-full space-y-4">
    <div class="flex justify-around bg-gray-50 p-4 rounded-lg border border-gray-200">
      </div>

    <div v-if="misplacedBooks.length > 0" class="bg-red-50 p-4 rounded-lg border border-red-100">
      <h3 class="font-bold text-red-800 mb-2 flex items-center gap-2">
        <span>⚠️</span> 조치 필요 도서
      </h3>
      <ul class="space-y-2">
        <li v-for="book in misplacedBooks" :key="book.detection_id" class="text-sm bg-white p-2 rounded shadow-sm flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="bg-red-100 text-red-800 font-bold text-[10px] w-5 h-5 flex items-center justify-center rounded-full">{{ book.detected_order }}</span>
            <span class="font-medium truncate max-w-[200px]">{{ book.ocr_call_number || book.ocr_title || '인식 불가' }}</span>
          </div>
          <span class="text-red-500 text-xs shrink-0">수정필요</span>
        </li>
      </ul>
    </div>
    
    <div v-if="matchedBooks.length > 0" class="bg-green-50 p-4 rounded-lg border border-green-100">
      <h3 class="font-bold text-green-800 mb-2 flex items-center gap-2">
        <span>✅</span> 정상 배가 도서
      </h3>
      <ul class="space-y-1">
        <li v-for="book in matchedBooks" :key="book.detection_id" class="text-xs bg-white p-2 rounded shadow-sm text-gray-600 flex items-center gap-2">
          <span class="bg-green-100 text-green-800 font-bold text-[9px] w-4 h-4 flex items-center justify-center rounded-full">{{ book.detected_order }}</span>
          <span class="truncate">{{ book.ocr_call_number || book.ocr_title }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
