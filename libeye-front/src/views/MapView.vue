<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getLocations, getMapStatus } from '../api/sessionAPI';

// 💡 1. 사용할 지도 이미지 import (이미지를 src/assets 폴더로 이동시켜주세요)
import mapImage from "../assets/img-floor-central-f3.png";

const router = useRouter();

// 💡 1. 선택된 위치 정보를 잠시 담아둘 변수 추가
const selectedLocationInfo = ref<any>(null);

// 모달 상태 관리
const showLevelModal = ref(false); // 단(Level) 선택 모달
const showModal = ref(false);      // 최종 상태/스캔 모달

const modalData = ref({ title: '', status: '', content: '' });
const locations = ref<any[]>([]);
const mapStatus = ref<any>({});
const selectedShelfGroup = ref<any>(null);

// 💡 2. 도면 위 책장 마커의 X, Y 좌표 매핑
// 팀의 실제 평면도(img-floor-central-f3.png) 위치에 맞게 top, left % 값을 조절해야 합니다.
const shelfCoordinates: Record<string, { top: string; left: string }> = {
  'A-1': { top: '35%', left: '25%' },
  'A-2': { top: '35%', left: '45%' },
  'A-3': { top: '35%', left: '65%' },
  'B-1': { top: '65%', left: '25%' },
  'B-2': { top: '65%', left: '45%' },
  // DB에 있는 section-shelf_num 조합을 여기에 모두 추가해주세요.
};

onMounted(async () => {
  try {
    locations.value = await getLocations();
    mapStatus.value = await getMapStatus();
  } catch (e) {
    console.error(e);
  }
});

// 💡 3. locations 데이터를 '책장(section-shelf_num)' 기준으로 묶어주기 (그룹화)
// 💡 locations 데이터를 묶어줄 때 '열' 글자를 제거합니다.
const groupedLocations = computed(() => {
  const groups: Record<string, { section: string; shelf_num: number; levels: any[] }> = {};
  
  locations.value.forEach(loc => {
    // 'B열' -> 'B' 로 문자열을 정리합니다.
    const cleanSection = loc.section.replace('열', '').trim();
    const key = `${cleanSection}-${loc.shelf_num}`;
    
    if (!groups[key]) {
      groups[key] = { section: cleanSection, shelf_num: loc.shelf_num, levels: [] };
    }
    groups[key].levels.push(loc);
  });
  
  // 각 책장 내에서 단(level_num)을 1단, 2단 순서로 정렬
  Object.values(groups).forEach(group => {
    group.levels.sort((a, b) => a.level_num - b.level_num);
  });
  
  return groups;
});

// 지도에서 책장 마커를 클릭했을 때
const openLevelModal = (group: any) => {
  selectedShelfGroup.value = group;
  showLevelModal.value = true;
};

// 특정 단(Level)을 클릭했을 때 기존 상태 모달 표시
// 특정 단(Level)을 클릭했을 때
const openStatusModal = (loc: any) => {
  showLevelModal.value = false; // 단 선택 모달은 닫기

  // 💡 2. 모달이 열릴 때 어떤 단(loc)을 클릭했는지 저장
  selectedLocationInfo.value = loc;
  
  const statusObj = mapStatus.value[loc.location_id] || { status: 'pending', error_count: 0 };
  const status = statusObj.status;
  
  // 💡 여기서도 원본 데이터(loc.section)에서 '열'을 제거하고 조립합니다.
  const cleanSection = loc.section.replace('열', '').trim();
  modalData.value.title = `${loc.room_name} ${cleanSection}열 ${loc.shelf_num}번 - ${loc.level_num}단`;
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

// 💡 3. 페이지 이동 시 query 파라미터 포함
const goToCamera = () => {
  if (selectedLocationInfo.value) {
    router.push({ 
      path: '/camera', 
      query: { locationId: selectedLocationInfo.value.location_id } 
    });
  } else {
    router.push('/camera'); // 만약 예외 상황으로 위치가 없으면 그냥 이동
  }
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

    <div class="flex-1 p-4 relative overflow-hidden flex items-center justify-center bg-stone-200">
      <div class="relative w-full max-w-lg aspect-[3/4] bg-white rounded-xl shadow-lg border border-stone-300 overflow-hidden">
        
        <img :src="mapImage" alt="Floor Map" class="w-full h-full object-cover opacity-90" />
        
        <div v-for="(group, key) in groupedLocations" :key="key"
             @click="openLevelModal(group)"
             class="absolute w-10 h-10 -ml-5 -mt-5 rounded-full bg-stone-900/80 text-white flex flex-col items-center justify-center cursor-pointer shadow-lg border-2 border-white transform transition active:scale-90 hover:bg-blue-600"
             :style="{ 
               top: shelfCoordinates[key]?.top || '50%', 
               left: shelfCoordinates[key]?.left || '50%' 
             }">
          <span class="text-xs font-bold">{{ group.section }}</span>
          <span class="text-[8px] leading-tight">{{ group.shelf_num }}</span>
        </div>
        
      </div>
    </div>

    <div v-if="showLevelModal" class="absolute inset-0 bg-stone-900/60 z-40 flex flex-col justify-end p-0 backdrop-blur-sm transition-all duration-300" @click.self="showLevelModal = false">
      <div class="bg-white w-full rounded-t-3xl p-6 shadow-2xl animate-slide-up flex flex-col max-h-[70vh]">
        
        <div class="flex justify-between items-center mb-5 shrink-0">
          <h2 class="text-xl font-extrabold text-stone-900">{{ selectedShelfGroup?.section }}열 {{ selectedShelfGroup?.shelf_num }}번 책장</h2>
          <button @click="showLevelModal = false" class="w-8 h-8 bg-stone-100 rounded-full text-stone-600 font-bold">✕</button>
        </div>
        
        <p class="text-xs text-stone-500 mb-3 shrink-0">작업할 단(층)을 선택해주세요.</p>
        
        <div class="grid grid-cols-2 gap-3 mb-4 overflow-y-auto pb-4 custom-scrollbar">
          <button v-for="loc in selectedShelfGroup?.levels" :key="loc.location_id" 
                  @click="openStatusModal(loc)"
                  class="p-4 rounded-xl flex items-center justify-between font-bold text-sm shadow-sm transition-transform active:scale-95"
                  :class="getStatusColor(loc.location_id)">
            <span>{{ loc.level_num }}단</span>
            <span v-if="mapStatus[loc.location_id]?.status === 'error'" class="text-lg">⚠</span>
            <span v-else-if="mapStatus[loc.location_id]?.status === 'done'" class="text-lg">✅</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="absolute inset-0 bg-stone-900/60 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
      <div class="bg-white w-full max-w-sm rounded-2xl p-5 shadow-2xl animate-pop-in">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h2 class="text-lg font-extrabold text-stone-900">{{ modalData.title }}</h2>
            <p class="text-[10px] text-stone-500">최근 점검: 시간 미상</p>
          </div>
          <button @click="showModal = false" class="w-6 h-6 bg-stone-100 rounded-full text-stone-600 font-bold">✕</button>
        </div>
        <div class="mb-5 text-sm rounded-xl p-4" 
             :class="{
               'bg-red-50 border border-red-200': modalData.status === 'error',
               'bg-green-50 border border-green-200': modalData.status === 'done',
               'bg-stone-100 border border-stone-200': modalData.status === 'pending'
             }"
             v-html="modalData.content"></div>
        <button @click="goToCamera" class="w-full bg-stone-800 text-white text-sm font-bold py-3.5 rounded-xl transition-colors hover:bg-stone-700">이 구역 스캔하기</button>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* 모달이 아래에서 위로 올라오는 애니메이션 (Tailwind 커스텀 또는 style 지정) */
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideUp {
  0% { transform: translateY(100%); }
  100% { transform: translateY(0); }
}
</style>
