<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getLocations, getMapStatus } from '../api/sessionAPI';
import { FLOORS } from '../constants/shelf';
import { groupLocations, buildGrid3F } from '../utils/shelfGrid';
import FloorTabs from '../components/map/FloorTabs.vue';
import MapLegend from '../components/map/MapLegend.vue';
import ShelfGridBoard from '../components/map/ShelfGridBoard.vue';
import LevelSelectModal from '../components/map/LevelSelectModal.vue';
import ShelfStatusModal from '../components/map/ShelfStatusModal.vue';

const router = useRouter();

// 💡 1. 층(Floor) 상태 관리 변수
const floors = FLOORS;
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
const groupedLocations = computed(() => groupLocations(locations.value));

// 💡 3. 새로운 엑셀 파일 기반 3층 그리드 레이아웃 생성 로직
const grid3F = computed(() => buildGrid3F(groupedLocations.value));

const currentGrid = computed(() => {
  if (currentFloor.value === '3F') return grid3F.value;
  return [];
});

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
      <FloorTabs :floors="floors" :current="currentFloor" @change="currentFloor = $event" />
    </header>

    <MapLegend />

    <div class="flex-1 overflow-auto p-6 bg-stone-200/50 relative">
      <ShelfGridBoard :grid="currentGrid" :map-status="mapStatus" @select-group="openLevelModal" />
    </div>

    <LevelSelectModal v-if="showLevelModal" :group="selectedShelfGroup" :map-status="mapStatus"
      @close="showLevelModal = false" @select-level="openStatusModal" />

    <ShelfStatusModal v-if="showModal" :data="modalData"
      @close="showModal = false" @go-history="goToHistory" @go-camera="goToCamera" />
  </main>
</template>
