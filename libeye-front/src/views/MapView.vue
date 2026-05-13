<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getLocations, getMapStatus } from '../api/sessionAPI';

const router = useRouter();
const showModal = ref(false);
const modalData = ref({ title: '', status: '', content: '' });
const locations = ref<any[]>([]);
const mapStatus = ref<any>({});

onMounted(async () => {
  try {
    locations.value = await getLocations();
    mapStatus.value = await getMapStatus();
  } catch (e) {
    console.error(e);
  }
});

const showShelfModal = (loc: any) => {
  const statusObj = mapStatus.value[loc.location_id] || { status: 'pending', error_count: 0 };
  const status = statusObj.status;
  
  modalData.value.title = `${loc.room_name} ${loc.section}열 ${loc.shelf_num}번`;
  modalData.value.status = status;
  
  if (status === 'error') {
    modalData.value.content = `<div class="font-bold text-red-800 mb-1">⚠ 조치 필요</div><ul class="text-red-700"><li>• 오류 ${statusObj.error_count}건</li></ul>`;
  } else if (status === 'done') {
    modalData.value.content = `<div class="font-bold text-green-800">✅ 점검 완료</div>`;
  } else {
    modalData.value.content = `<div class="font-bold text-stone-800">미점검 상태</div>`;
  }
  
  showModal.value = true;
};

const goToCamera = () => {
  router.push('/camera');
};

const getStatusColor = (locId: string) => {
  const s = mapStatus.value[locId]?.status;
  if (s === 'done') return 'bg-[#2E7D32] text-white';
  if (s === 'error') return 'bg-[#D32F2F] text-white ring-2 ring-red-500/20';
  return 'bg-stone-200 border border-stone-300 text-stone-500';
};
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 bg-stone-100 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <h1 class="text-xl font-extrabold text-stone-900">서고 작업 지도</h1>
    </header>
    <div class="bg-white px-5 py-2 border-b border-stone-100 flex gap-3 text-[9px] font-bold text-stone-600 shrink-0">
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-stone-200 border border-stone-300"></span> 미점검</div>
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#2E7D32]"></span> 정상</div>
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#D32F2F]"></span> 오류 발생</div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 relative">
      <div class="grid grid-cols-3 gap-x-3 gap-y-5 mb-20 relative z-10">
        <div v-for="loc in locations" :key="loc.location_id" 
             @click="showShelfModal(loc)" 
             class="h-16 rounded flex flex-col items-center justify-center font-bold text-xs cursor-pointer active:scale-95 transition-transform"
             :class="getStatusColor(loc.location_id)">
          <span>{{ loc.section }}-{{ loc.shelf_num }}</span>
          <span class="text-[9px] font-normal opacity-80">{{ loc.level_num }}단</span>
        </div>
      </div>
    </div>

    <!-- Map Modal -->
    <div v-if="showModal" class="absolute inset-0 bg-stone-900/40 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
      <div class="bg-white w-full rounded-2xl p-5 shadow-2xl animate-pop-in">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h2 class="text-lg font-extrabold text-stone-900">{{ modalData.title }}</h2>
            <p class="text-[10px] text-stone-500">최근 점검: 14:15</p>
          </div>
          <button @click="showModal = false" class="w-6 h-6 bg-stone-100 rounded-full text-stone-600 font-bold">✕</button>
        </div>
        <div class="mb-4 text-xs rounded-xl p-3" 
             :class="{
               'bg-red-50 border border-red-200': modalData.status === 'error',
               'bg-green-50 border border-green-200': modalData.status === 'done',
               'bg-stone-100 border border-stone-200': modalData.status === 'pending'
             }"
             v-html="modalData.content"></div>
        <button @click="goToCamera" class="w-full bg-stone-800 text-white text-xs font-bold py-3 rounded-xl">이 구역 스캔하기</button>
      </div>
    </div>
  </main>
</template>
