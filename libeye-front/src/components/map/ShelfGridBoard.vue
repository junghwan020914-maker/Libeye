<script setup lang="ts">
import { SECTION_LABELS } from '../../constants/shelf';

const props = defineProps<{ grid: any[][]; mapStatus: any }>();
const emit = defineEmits<{ (e: 'select-group', group: any): void }>();

const getShelfGroupColor = (group: any) => {
  if (!group || group.levels.length === 0) return 'bg-white border-dashed border-2 border-stone-300 text-stone-400';

  let hasError = false;
  let allDone = true;

  group.levels.forEach((loc: any) => {
    const s = props.mapStatus[loc.location_id]?.status;
    if (s === 'error') hasError = true;
    if (s !== 'done') allDone = false;
  });

  if (hasError) return 'bg-[#D32F2F] text-white border-transparent shadow-md ring-2 ring-red-500/30';
  if (allDone) return 'bg-[#2E7D32] text-white border-transparent shadow-md';
  return 'bg-stone-200 border-stone-300 text-stone-700 shadow-sm';
};
</script>

<template>
  <div v-if="grid.length > 0" class="inline-block bg-white p-6 rounded-2xl shadow-sm border border-stone-200 min-w-max">

    <div class="grid grid-cols-7 gap-3 mb-3">
      <div v-for="col in SECTION_LABELS" :key="col"
           class="text-center font-extrabold text-stone-400 text-sm">
        {{ col }}
      </div>
    </div>

    <div class="grid grid-cols-7 gap-3">
      <template v-for="(row, rIndex) in grid" :key="'row-'+rIndex">
        <div v-for="(cell, cIndex) in row" :key="'cell-'+rIndex+'-'+cIndex" class="relative group">
          <button v-if="cell"
                  @click="emit('select-group', cell)"
                  class="w-12 h-12 rounded-xl flex items-center justify-center text-xs font-bold transition-transform active:scale-95 border"
                  :class="getShelfGroupColor(cell)">
            {{ cell.shelf_num }}
          </button>
          <div v-else class="w-12 h-12 bg-transparent"></div>
        </div>
      </template>
    </div>
  </div>

  <div v-else class="h-full flex flex-col items-center justify-center text-stone-400">
    <svg class="w-12 h-12 mb-3 opacity-20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 12h3v8h14v-8h3L12 2z"/></svg>
    <p class="font-bold">도면 데이터를 준비 중입니다.</p>
  </div>
</template>
