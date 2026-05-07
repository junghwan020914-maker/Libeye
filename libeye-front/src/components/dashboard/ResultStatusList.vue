<script setup lang="ts">
import { computed } from 'vue';
import type { DetectionResult } from '../../types/session';

const props = defineProps<{
  detections: DetectionResult[];
}>();

// 상태별로 도서 분류하기
const matchedBooks = computed(() => props.detections.filter(d => d.status === 'MATCH'));
const misplacedBooks = computed(() => props.detections.filter(d => d.status === 'MISPLACED'));
const unknownBooks = computed(() => props.detections.filter(d => d.status === 'UNKNOWN' || d.status === 'MISSING'));
</script>

<template>
  <div class="mt-6 w-full space-y-4">
    <!-- 상태 요약 헤더 -->
    <div class="flex justify-around bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div class="text-center">
        <div class="text-2xl font-bold text-green-600">{{ matchedBooks.length }}</div>
        <div class="text-xs text-gray-500">정상 (MATCH)</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold text-red-600">{{ misplacedBooks.length }}</div>
        <div class="text-xs text-gray-500">오배열 (MISPLACED)</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold text-yellow-600">{{ unknownBooks.length }}</div>
        <div class="text-xs text-gray-500">확인필요</div>
      </div>
    </div>

    <!-- 오배열 목록 (우선순위 높음) -->
    <div v-if="misplacedBooks.length > 0" class="bg-red-50 p-4 rounded-lg border border-red-100">
      <h3 class="font-bold text-red-800 mb-2 flex items-center gap-2">
        <span>⚠️</span> 조치 필요 도서
      </h3>
      <ul class="space-y-2">
        <li v-for="book in misplacedBooks" :key="book.detection_id" class="text-sm bg-white p-2 rounded shadow-sm flex justify-between">
          <span class="font-medium">인식: {{ book.ocr_text }}</span>
          <span class="text-red-500 text-xs">수정필요</span>
        </li>
      </ul>
    </div>
    
    <!-- 정상 목록 (접어두기 가능하게 구현 가능) -->
    <div v-if="matchedBooks.length > 0" class="bg-green-50 p-4 rounded-lg border border-green-100">
      <h3 class="font-bold text-green-800 mb-2 flex items-center gap-2">
        <span>✅</span> 정상 배가 도서
      </h3>
      <ul class="space-y-1">
        <li v-for="book in matchedBooks" :key="book.detection_id" class="text-xs bg-white p-2 rounded shadow-sm text-gray-600">
          {{ book.ocr_text }}
        </li>
      </ul>
    </div>
  </div>
</template>
