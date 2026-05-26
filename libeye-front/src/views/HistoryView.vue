<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getHistory } from '../api/sessionAPI';

const router = useRouter();
const route = useRoute();
const historyList = ref<any[]>([]);

type FilterKey = 'all' | 'pending' | 'completed';
const activeFilter = ref<FilterKey>('all');

// 서버 응답이 아직 오지 않은(분석 중) 세션 판별
// ScanSession.status: PENDING / PROCESSING / COMPLETED / FAILED
const isAnalyzing = (item: any) => {
  const s = (item?.status ?? '').toString().toUpperCase();
  return s !== 'COMPLETED' && s !== 'FAILED';
};

// 상태 우선순위: 분석 중 → 미결 → 완료
const statusOf = (item: any): 'analyzing' | 'unresolved' | 'done' => {
  if (isAnalyzing(item)) return 'analyzing';
  if ((item?.error_count ?? 0) > 0) return 'unresolved';
  return 'done';
};

const filteredList = computed(() => {
  if (activeFilter.value === 'all') return historyList.value;
  if (activeFilter.value === 'pending') {
    // "조치 필요"는 완료된 세션 중 오류가 있는 항목만 (분석 중은 제외)
    return historyList.value.filter(item => statusOf(item) === 'unresolved');
  }
  // "완료"는 분석이 끝났고 오류가 없는 항목만 (분석 중은 제외)
  return historyList.value.filter(item => statusOf(item) === 'done');
});

const tabClass = (key: FilterKey) =>
  activeFilter.value === key
    ? 'px-4 py-1.5 rounded-full bg-stone-800 text-white text-[11px] font-bold'
    : 'px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold';

onMounted(async () => {
  try {
    const locationId = route.query.locationId as string;
    historyList.value = await getHistory(locationId);
  } catch (err) {
    console.error(err);
  }
});
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 bg-stone-50 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <h1 class="text-xl font-extrabold text-stone-900">스캔 히스토리</h1>
      <div class="flex gap-2 mt-4 overflow-x-auto no-scrollbar pb-1">
        <button :class="tabClass('all')" @click="activeFilter = 'all'">전체보기</button>
        <button :class="tabClass('pending')" @click="activeFilter = 'pending'">조치 필요 ⚠️</button>
        <button :class="tabClass('completed')" @click="activeFilter = 'completed'">완료 ✅</button>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-stone-100/50">
      <div v-for="item in filteredList" :key="item.session_id" @click="router.push(`/detail?sessionId=${item.session_id}`)"
           class="bg-white rounded-xl shadow-sm border border-stone-200 p-4 flex items-center justify-between cursor-pointer active:scale-[0.98]"
           :class="{
             'border-l-4 border-l-red-500': statusOf(item) === 'unresolved',
             'border-l-4 border-l-amber-400': statusOf(item) === 'analyzing'
           }">
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <h3 class="font-extrabold text-stone-900 text-sm">{{ item.location_id }}</h3>
            <span v-if="statusOf(item) === 'analyzing'" class="text-[9px] font-bold bg-amber-100 text-amber-700 px-1 rounded">분석 중</span>
            <span v-else-if="statusOf(item) === 'unresolved'" class="text-[9px] font-bold bg-red-100 text-red-700 px-1 rounded">미결</span>
            <span v-else class="text-[9px] font-bold bg-green-100 text-green-700 px-1 rounded">완료</span>
          </div>
          <p class="text-[10px] font-medium text-stone-500">
            {{ new Date(item.created_at).toLocaleString() }}
            <template v-if="statusOf(item) !== 'analyzing'"> · 총 {{ item.total_count }}권 스캔</template>
          </p>
          <div class="flex gap-1 mt-1">
            <span v-if="statusOf(item) === 'analyzing'" class="px-1.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-200 rounded text-[9px] font-bold">⏳ 분석 진행 중</span>
            <span v-else-if="statusOf(item) === 'unresolved'" class="px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-[9px] font-bold">⚠ 오류 {{ item.error_count }}건</span>
            <span v-else class="px-1.5 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded text-[9px] font-bold">✅ 전체 정상</span>
          </div>
        </div>
        <div class="text-stone-300 text-xl font-bold">❯</div>
      </div>

      <div v-if="filteredList.length === 0" class="text-stone-500 text-center py-10">
        히스토리가 없습니다.
      </div>
    </div>
  </main>
</template>
