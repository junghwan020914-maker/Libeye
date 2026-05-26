<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // useRoute 추가
import { getHistory } from '../api/sessionAPI';

const router = useRouter();
const route = useRoute(); // route 객체 초기화
const historyList = ref<any[]>([]);

onMounted(async () => {
  try {
    // URL에서 ?locationId= 값을 가져옵니다.
    const locationId = route.query.locationId as string;
    
    // 가져온 locationId를 API 함수에 전달합니다.
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
        <button class="px-4 py-1.5 rounded-full bg-stone-800 text-white text-[11px] font-bold">전체보기</button>
        <button class="px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold">조치 필요 ⚠️</button>
        <button class="px-4 py-1.5 rounded-full bg-white border border-stone-200 text-stone-600 text-[11px] font-bold">완료 ✅</button>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-stone-100/50">
      <div v-for="item in historyList" :key="item.session_id" @click="router.push(`/detail?sessionId=${item.session_id}`)" 
           class="bg-white rounded-xl shadow-sm border border-stone-200 p-4 flex items-center justify-between cursor-pointer active:scale-[0.98]"
           :class="{'border-l-4 border-l-red-500': item.error_count > 0}">
        <div class="flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <h3 class="font-extrabold text-stone-900 text-sm">{{ item.location_id }}</h3>
            <span v-if="item.error_count > 0" class="text-[9px] font-bold bg-red-100 text-red-700 px-1 rounded">미결</span>
            <span v-else class="text-[9px] font-bold bg-green-100 text-green-700 px-1 rounded">완료</span>
          </div>
          <p class="text-[10px] font-medium text-stone-500">{{ new Date(item.created_at).toLocaleString() }} · 총 {{ item.total_count }}권 스캔</p>
          <div class="flex gap-1 mt-1">
            <span v-if="item.error_count > 0" class="px-1.5 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-[9px] font-bold">⚠ 오류 {{ item.error_count }}건</span>
            <span v-else class="px-1.5 py-0.5 bg-green-50 text-green-700 border border-green-200 rounded text-[9px] font-bold">✅ 전체 정상</span>
          </div>
        </div>
        <div class="text-stone-300 text-xl font-bold">❯</div>
      </div>
      
      <div v-if="historyList.length === 0" class="text-stone-500 text-center py-10">
        히스토리가 없습니다.
      </div>
    </div>
  </main>
</template>
