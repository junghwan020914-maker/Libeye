<script setup lang="ts">
import type { SessionFilterKey } from '../../types/history';

const props = defineProps<{ active: SessionFilterKey }>();
const emit = defineEmits<{ (e: 'change', key: SessionFilterKey): void }>();

const tabClass = (key: SessionFilterKey) =>
  props.active === key
    ? 'px-4 py-1.5 rounded-full bg-stone-800 text-white text-[11px] font-bold'
    : 'px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold';
</script>

<template>
  <div class="flex gap-2 mt-4 overflow-x-auto no-scrollbar pb-1">
    <button :class="tabClass('all')" @click="emit('change', 'all')">전체보기</button>
    <button :class="tabClass('pending')" @click="emit('change', 'pending')">조치 필요 ⚠️</button>
    <button :class="tabClass('completed')" @click="emit('change', 'completed')">완료 ✅</button>
  </div>
</template>
