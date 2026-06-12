<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getHistory } from '../api/sessionAPI';
import { statusOf } from '../utils/sessionStatus';
import type { SessionFilterKey } from '../types/history';
import HistoryFilterTabs from '../components/history/HistoryFilterTabs.vue';
import SessionHistoryCard from '../components/history/SessionHistoryCard.vue';

const router = useRouter();
const route = useRoute();
const historyList = ref<any[]>([]);

const activeFilter = ref<SessionFilterKey>('all');

const filteredList = computed(() => {
  if (activeFilter.value === 'all') return historyList.value;
  if (activeFilter.value === 'pending') {
    // "조치 필요"는 완료된 세션 중 오류가 있는 항목만 (분석 중은 제외)
    return historyList.value.filter(item => statusOf(item) === 'unresolved');
  }
  // "완료"는 분석이 끝났고 오류가 없는 항목만 (분석 중은 제외)
  return historyList.value.filter(item => statusOf(item) === 'done');
});

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
      <HistoryFilterTabs :active="activeFilter" @change="activeFilter = $event" />
    </header>

    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-stone-100/50">
      <SessionHistoryCard v-for="item in filteredList" :key="item.session_id" :item="item"
        @open="router.push(`/detail?sessionId=${item.session_id}`)" />

      <div v-if="filteredList.length === 0" class="text-stone-500 text-center py-10">
        히스토리가 없습니다.
      </div>
    </div>
  </main>
</template>
