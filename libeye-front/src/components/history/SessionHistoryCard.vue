<script setup lang="ts">
import { statusOf } from '../../utils/sessionStatus';

defineProps<{ item: any }>();
const emit = defineEmits<{ (e: 'open'): void }>();
</script>

<template>
  <div @click="emit('open')"
       class="bg-white rounded-xl shadow-sm border border-stone-200 p-4 flex items-center justify-between cursor-pointer active:scale-[0.98]"
       :class="{
         'border-l-4 border-l-red-500': statusOf(item) === 'unresolved',
         'border-l-4 border-l-amber-400': statusOf(item) === 'analyzing',
         'border-l-4 border-l-gray-400': statusOf(item) === 'failed'
       }">
    <div class="flex flex-col gap-1">
      <div class="flex items-center gap-2">
        <h3 class="font-extrabold text-stone-900 text-sm">{{ item.location_id }}</h3>
        <span v-if="statusOf(item) === 'analyzing'" class="text-[9px] font-bold bg-amber-100 text-amber-700 px-1 rounded">분석 중</span>
        <span v-else-if="statusOf(item) === 'failed'" class="text-[9px] font-bold bg-gray-100 text-gray-600 px-1 rounded">실패</span>
        <span v-else-if="statusOf(item) === 'unresolved'" class="text-[9px] font-bold bg-red-100 text-red-700 px-1 rounded">미결</span>

        <span v-else-if="item.has_batch_action" class="text-[9px] font-bold bg-stone-200 text-stone-700 px-1 rounded">일괄완료</span>

        <span v-else class="text-[9px] font-bold bg-green-100 text-green-700 px-1 rounded">완료</span>
      </div>
      <p class="text-[10px] font-medium text-stone-500">
        {{ new Date(item.created_at).toLocaleString() }}
        <template v-if="statusOf(item) !== 'analyzing'"> · 총 {{ item.total_count }}권 스캔</template>
      </p>
      <div class="flex gap-1 mt-1">
        <span v-if="statusOf(item) === 'analyzing'" class="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded text-[9px] font-bold">⏳ 분석 진행 중</span>
        <span v-else-if="statusOf(item) === 'failed'" class="px-1.5 py-0.5 bg-gray-50 text-gray-500 border border-gray-200 rounded text-[9px] font-bold">✗ 분석 실패</span>
        <span v-else-if="statusOf(item) === 'unresolved'" class="px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-[9px] font-bold">⚠ 오류 {{ item.error_count }}건</span>

        <span v-else-if="item.has_batch_action" class="px-1.5 py-0.5 bg-stone-100 text-stone-700 border border-stone-300 rounded text-[9px] font-bold">✅ 일괄 강제 완료</span>

        <span v-else class="px-1.5 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded text-[9px] font-bold">✅ 전체 정상</span>
      </div>
    </div>
    <div class="text-stone-300 text-xl font-bold">❯</div>
  </div>
</template>
