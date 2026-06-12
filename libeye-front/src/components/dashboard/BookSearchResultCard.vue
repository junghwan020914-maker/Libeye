<script setup lang="ts">
import { formatDateTime } from '../../utils/datetime';

defineProps<{ book: any }>();
</script>

<template>
  <div
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
          <span>⏱️ 최종 확인</span>
        </span>
        <span class="font-medium text-stone-500">{{ formatDateTime(book.last_seen_time) }}</span>
      </div>
    </div>

  </div>
</template>
