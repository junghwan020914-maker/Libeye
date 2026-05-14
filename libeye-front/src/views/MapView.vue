<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getLocations, getMapStatus } from '../api/sessionAPI';

const router = useRouter();

// 💡 1. 층(Floor) 상태 관리 변수
const floors = ['B2', 'B1', '1F', '2F', '3F'];
const currentFloor = ref('3F'); // 기본 선택 층

// API 데이터 및 선택 상태
const locations = ref<any[]>([]);
const mapStatus = ref<any>({});
const selectedLocationInfo = ref<any>(null);
const selectedShelfGroup = ref<any>(null);

// 모달 상태
const showLevelModal = ref(false);
const showModal = ref(false);
const modalData = ref({ title: '', status: '', content: '' });

onMounted(async () => {
  try {
    locations.value = await getLocations();
    mapStatus.value = await getMapStatus();
  } catch (e) {
    console.error(e);
  }
});

// 💡 2. API locations 데이터를 '책장(Section-Shelf_num)' 기준으로 그룹화
const groupedLocations = computed(() => {
  const groups: Record<string, { section: string; shelf_num: number; levels: any[] }> = {};
  
  locations.value.forEach(loc => {
    const cleanSection = loc.section.replace('열', '').trim();
    const key = `${cleanSection}-${loc.shelf_num}`; 
    
    if (!groups[key]) {
      groups[key] = { section: cleanSection, shelf_num: loc.shelf_num, levels: [] };
    }
    groups[key].levels.push(loc);
  });
  
  // 각 책장 내에서 단(level_num)을 1단~5단 순서로 정렬
  Object.values(groups).forEach(group => {
    group.levels.sort((a, b) => a.level_num - b.level_num);
  });
  
  return groups;
});

// 💡 3. 새로운 엑셀 파일 기반 3층 그리드 레이아웃 생성 로직
const grid3F = computed(() => {
  const grid = [];
  const sections = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
  
  for (let r = 1; r <= 32; r++) {
    const row = [];
    for (let c = 0; c < 7; c++) {
      let hasShelf = false;
      
      if (c === 0) hasShelf = true; // A열 (1~32행)
      if (c === 1) hasShelf = true; // B열 (1~32행)
      if (c === 2 && r >= 5) hasShelf = true;  // C열 (5~32행)
      if (c === 3 && r >= 13) hasShelf = true; // D열 (13~32행)
      if (c === 4 && r >= 19) hasShelf = true; // E열 (19~32행)
      if (c === 5 && r >= 25) hasShelf = true; // F열 (25~32행)
      if (c === 6 && r >= 25) hasShelf = true; // G열 (25~32행)
      
      if (hasShelf) {
        const section = sections[c];
        const key = `${section}-${r}`;
        const groupData = groupedLocations.value[key] || { section, shelf_num: r, levels: [] };
        row.push(groupData);
      } else {
        row.push(null); 
      }
    }
    grid.push(row);
  }
  return grid;
});

const currentGrid = computed(() => {
  if (currentFloor.value === '3F') return grid3F.value;
  return []; 
});

const getShelfGroupColor = (group: any) => {
  if (!group || group.levels.length === 0) return 'bg-white border-dashed border-2 border-stone-300 text-stone-400';
  
  let hasError = false;
  let allDone = true;
  
  group.levels.forEach((loc: any) => {
    const s = mapStatus.value[loc.location_id]?.status;
    if (s === 'error') hasError = true;
    if (s !== 'done') allDone = false;
  });

  if (hasError) return 'bg-[#D32F2F] text-white border-transparent shadow-md ring-2 ring-red-500/30';
  if (allDone) return 'bg-[#2E7D32] text-white border-transparent shadow-md';
  return 'bg-stone-200 border-stone-300 text-stone-700 shadow-sm';
};

const getLevelColor = (locId: string) => {
  const s = mapStatus.value[locId]?.status;
  if (s === 'done') return 'bg-[#2E7D32] text-white';
  if (s === 'error') return 'bg-[#D32F2F] text-white ring-2 ring-red-500/20';
  return 'bg-stone-200 border border-stone-300 text-stone-500';
};

const openLevelModal = (group: any) => {
  if (!group || group.levels.length === 0) {
    alert("해당 구역의 도서 데이터가 DB에 없습니다.");
    return;
  }
  selectedShelfGroup.value = group;
  showLevelModal.value = true;
};

const openStatusModal = (loc: any) => {
  showLevelModal.value = false;
  selectedLocationInfo.value = loc;
  
  const statusObj = mapStatus.value[loc.location_id] || { status: 'pending', error_count: 0 };
  const status = statusObj.status;
  const cleanSection = loc.section.replace('열', '').trim();
  
  modalData.value.title = `${loc.room_name || currentFloor.value} ${cleanSection}열 ${loc.shelf_num}번 - ${loc.level_num}단`;
  modalData.value.status = status;
  
  if (status === 'error') {
    modalData.value.content = `<div class="font-bold text-red-800 mb-1">⚠ 조치 필요</div><ul class="text-red-700"><li>• 오류 ${statusObj.error_count}건 발생</li></ul>`;
  } else if (status === 'done') {
    modalData.value.content = `<div class="font-bold text-green-800">✅ 점검 완료</div>`;
  } else {
    modalData.value.content = `<div class="font-bold text-stone-800">미점검 상태</div>`;
  }
  
  showModal.value = true;
};

// 💡 4. 라우팅 로직 (스캔 & 기록 보기)
const goToCamera = () => {
  if (selectedLocationInfo.value) {
    router.push({ path: '/camera', query: { locationId: selectedLocationInfo.value.location_id } });
  } else {
    router.push('/camera');
  }
};

const goToHistory = () => {
  if (selectedLocationInfo.value) {
    router.push({ path: '/history', query: { locationId: selectedLocationInfo.value.location_id } });
  } else {
    router.push('/history');
  }
};
</script>

<template>
  <main class="flex-col h-full animate-fade-in bg-stone-100 flex overflow-hidden pb-20">
    
    <header class="bg-white border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <div class="px-5 py-4">
        <h1 class="text-xl font-extrabold text-stone-900">서고 작업 지도</h1>
      </div>
      <div class="flex overflow-x-auto hide-scrollbar px-4 pb-2 gap-2">
        <button v-for="floor in floors" :key="floor"
                @click="currentFloor = floor"
                class="px-5 py-2 rounded-full text-sm font-bold transition-colors whitespace-nowrap"
                :class="currentFloor === floor ? 'bg-stone-800 text-white shadow-md' : 'bg-stone-100 text-stone-500 hover:bg-stone-200'">
          {{ floor }}
        </button>
      </div>
    </header>
    
    <div class="bg-white px-5 py-2.5 border-b border-stone-200 flex justify-between text-[10px] font-bold text-stone-600 shrink-0 shadow-sm z-10">
      <div class="flex gap-4">
        <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#2E7D32]"></span> 정상</div>
        <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-[#D32F2F]"></span> 오류 발생</div>
        <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-stone-200 border border-stone-300"></span> 미점검</div>
      </div>
    </div>

    <div class="flex-1 overflow-auto p-6 bg-stone-200/50 relative">
      <div v-if="currentGrid.length > 0" class="inline-block bg-white p-6 rounded-2xl shadow-sm border border-stone-200 min-w-max">
        
        <div class="grid grid-cols-7 gap-3 mb-3">
          <div v-for="col in ['A열', 'B열', 'C열', 'D열', 'E열', 'F열', 'G열']" :key="col" 
               class="text-center font-extrabold text-stone-400 text-sm">
            {{ col }}
          </div>
        </div>

        <div class="grid grid-cols-7 gap-3">
          <template v-for="(row, rIndex) in currentGrid" :key="'row-'+rIndex">
            <div v-for="(cell, cIndex) in row" :key="'cell-'+rIndex+'-'+cIndex" class="relative group">
              <button v-if="cell" 
                      @click="openLevelModal(cell)"
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
    </div>

    <div v-if="showLevelModal" class="absolute inset-0 bg-stone-900/60 z-40 flex flex-col justify-end p-0 backdrop-blur-sm transition-all duration-300" @click.self="showLevelModal = false">
      <div class="bg-white w-full rounded-t-3xl p-6 shadow-2xl animate-slide-up flex flex-col max-h-[65vh] mb-20">
        
        <div class="flex justify-between items-center mb-5 shrink-0">
          <h2 class="text-xl font-extrabold text-stone-900">{{ selectedShelfGroup?.section }}열 {{ selectedShelfGroup?.shelf_num }}번 책장</h2>
          <button @click="showLevelModal = false" class="w-8 h-8 bg-stone-100 rounded-full text-stone-600 font-bold hover:bg-stone-200">✕</button>
        </div>
        
        <p class="text-xs text-stone-500 mb-4 shrink-0">작업할 단(층)을 선택해주세요.</p>
        
        <div class="flex flex-col-reverse gap-3 overflow-y-auto pb-4 custom-scrollbar">
          <button v-for="loc in selectedShelfGroup?.levels" :key="loc.location_id" 
                  @click="openStatusModal(loc)"
                  class="p-4 rounded-xl flex items-center justify-between font-bold text-sm shadow-sm transition-transform active:scale-95"
                  :class="getLevelColor(loc.location_id)">
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
          </div>
          <button @click="showModal = false" class="w-6 h-6 bg-stone-100 hover:bg-stone-200 rounded-full text-stone-600 font-bold flex items-center justify-center">✕</button>
        </div>
        <div class="mb-5 text-sm rounded-xl p-4" 
             :class="{
               'bg-red-50 border border-red-200': modalData.status === 'error',
               'bg-green-50 border border-green-200': modalData.status === 'done',
               'bg-stone-100 border border-stone-200': modalData.status === 'pending'
             }"
             v-html="modalData.content"></div>
        <div class="flex gap-3">
          <button @click="goToHistory" 
                  class="flex-1 bg-white border border-stone-300 text-stone-700 text-sm font-bold py-3.5 rounded-xl transition-colors hover:bg-stone-50 shadow-sm">
            최근 기록 보기
          </button>
          <button @click="goToCamera" 
                  class="flex-1 bg-stone-800 text-white text-sm font-bold py-3.5 rounded-xl transition-colors hover:bg-stone-700 shadow-sm">
            스캔하기
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideUp {
  0% { transform: translateY(100%); }
  100% { transform: translateY(0); }
}
.animate-pop-in {
  animation: popIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes popIn {
  0% { opacity: 0; transform: scale(0.95); }
  100% { opacity: 1; transform: scale(1); }
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d6d3d1;
  border-radius: 10px;
}
</style>
