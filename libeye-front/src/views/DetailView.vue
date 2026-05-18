<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisPolling } from '../composables/useAnalysisPolling';

const route = useRoute();
const router = useRouter();

const sessionId = computed(() => route.query.sessionId as string | null);
const { data: sessionData, isError } = useAnalysisPolling(sessionId);

const showEditModal = ref(false);

const goBack = () => {
  router.push('/history');
};

// --- [추가된 핵심 로직] 이미지 해상도 비율 및 오프셋 계산 ---
const imageDimensions = ref<Record<string, { scaleX: number, scaleY: number, offsetX: number, offsetY: number }>>({});

const onImageLoad = (event: Event, imageId: string) => {
  const img = event.target as HTMLImageElement;
  
  // 1. 화면에 표시된 컨테이너 크기 vs 실제 원본 이미지 크기
  const containerW = img.clientWidth;
  const containerH = img.clientHeight;
  const naturalW = img.naturalWidth;
  const naturalH = img.naturalHeight;

  // 2. object-contain으로 인한 스케일 비율 계산
  const containerRatio = containerW / containerH;
  const imageRatio = naturalW / naturalH;

  let renderedW, renderedH, offsetX = 0, offsetY = 0;

  if (imageRatio > containerRatio) {
    // 이미지가 컨테이너보다 가로로 길 때 (상하 여백 발생)
    renderedW = containerW;
    renderedH = containerW / imageRatio;
    offsetY = (containerH - renderedH) / 2;
  } else {
    // 이미지가 컨테이너보다 세로로 길 때 (좌우 여백 발생)
    renderedH = containerH;
    renderedW = containerH * imageRatio;
    offsetX = (containerW - renderedW) / 2;
  }

  // 3. 변환된 스케일과 오프셋 저장
  imageDimensions.value[imageId] = {
    scaleX: renderedW / naturalW,
    scaleY: renderedH / naturalH,
    offsetX,
    offsetY
  };
};

// --- [추가된 핵심 로직] YOLO 좌표를 CSS 픽셀로 변환 ---
const getBoxStyle = (detection: any, imageId: string) => {
  const dim = imageDimensions.value[imageId];
  
  // 이미지가 아직 로드되지 않았거나 bounding_box 값이 없으면 렌더링 숨김
  if (!dim || !detection.bounding_box) return { display: 'none' };
  
  // DB에서 JSON 문자열로 넘어올 경우를 대비한 안전한 파싱
  const box = typeof detection.bounding_box === 'string' 
    ? JSON.parse(detection.bounding_box) 
    : detection.bounding_box;

  return {
    position: 'absolute',
    left: `${dim.offsetX + (box.x * dim.scaleX)}px`,
    top: `${dim.offsetY + (box.y * dim.scaleY)}px`,
    width: `${box.w * dim.scaleX}px`,
    height: `${box.h * dim.scaleY}px`,
  };
};

</script>

<template>
  <main class="flex-col h-full bg-stone-50 z-30 animate-fade-in absolute inset-0 w-full flex">
    <header class="bg-white px-4 py-3 border-b border-stone-200 flex items-center justify-between shrink-0">
      <button @click="goBack" class="p-2 text-stone-600 text-xl font-bold">◀</button>
      <div class="text-center">
        <h1 class="text-sm font-extrabold text-stone-900">상세 분석 및 조치</h1>
    
    	<p class="text-[9px] text-stone-500">
	  {{ sessionData?.location_name || sessionData?.location_id || '위치 정보 로딩 중...' }}
    	</p>
  	</div>
  	<div class="w-10"></div>
    </header>

    <!-- Polling Loading State -->
    <div v-if="(sessionData?.status?.toUpperCase() !== 'COMPLETED' && sessionData?.status?.toUpperCase() !== 'SUCCESS') && !isError" class="flex-1 flex flex-col items-center justify-center p-6 bg-stone-900/90 text-white">
      <div class="w-16 h-16 border-4 border-stone-600 border-t-green-500 rounded-full animate-spin mb-6"></div>
      <h2 class="font-extrabold text-lg tracking-wide animate-pulse">Vision AI 분석 중...</h2>
      <p class="text-stone-400 text-xs mt-2">청구기호 해독 및 배가 상태 비교</p>
    </div>

    <!-- Error State -->
    <div v-else-if="isError" class="flex-1 flex flex-col items-center justify-center p-6">
      <p class="text-red-500 font-bold text-lg">서버 연결 오류</p>
      <button @click="router.push('/camera')" class="mt-4 px-6 py-3 bg-stone-200 rounded-xl text-stone-700 font-bold">다시 시도하기</button>
    </div>

    <!-- Results State -->
    <template v-else-if="sessionData">
      <div class="h-48 bg-stone-300 relative flex overflow-x-auto overflow-y-hidden snap-x shrink-0 shadow-inner scrollbar-hide">
        
        <div v-if="!sessionData.images || sessionData.images.length === 0" class="absolute inset-0 flex justify-center items-center opacity-30 text-5xl w-full">📚📚📚</div>
        
        <div v-for="img in sessionData.images" :key="img.image_id" 
             class="relative h-full min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center border-r-2 border-stone-800/40">
          
          <img :src="img.image_url" @load="(e) => onImageLoad(e, img.image_id)" class="absolute inset-0 w-full h-full object-contain opacity-50" />
          
          <template v-for="d in sessionData.detections" :key="d.detection_id">
            <div v-if="d.source_image_id === img.image_id"
                 class="ar-box absolute flex justify-center z-10 transition-all hover:scale-105"
                 :style="getBoxStyle(d, img.image_id)"
                 :class="{
                   'border-2 border-[#2E7D32] bg-green-500/10': d.status === 'MATCH',
                   'border-2 border-[#D32F2F] bg-red-500/30 shadow-[0_0_15px_rgba(211,47,47,0.4)]': d.status === 'MISPLACED',
                   'border-2 border-[#F57C00] bg-orange-500/30': d.status === 'UNKNOWN' || d.status === 'MISSING'
                 }">
                 
              <span class="absolute -top-6 bg-stone-800 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full font-bold shadow-md">
                {{ d.detected_order }}
              </span>
              <span v-if="d.status !== 'MATCH'" class="absolute -top-5 left-6 bg-white border text-[8px] px-1 rounded whitespace-nowrap"
                    :class="{
                      'border-[#D32F2F] text-[#D32F2F]': d.status === 'MISPLACED',
                      'border-[#F57C00] text-[#F57C00]': d.status === 'UNKNOWN' || d.status === 'MISSING'
                    }">
                {{ d.status === 'MISPLACED' ? '오배열' : '확인요망' }}
              </span>
            </div>
          </template>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 pb-20">
        <div class="flex flex-col gap-2">
          <!-- Iterate over detections and show cards for errors -->
          <template v-for="d in sessionData.detections" :key="d.detection_id">
            <div v-if="d.status === 'MISPLACED'" class="bg-red-50 p-3 rounded-lg border border-red-200 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img v-if="d.crop_image_url" :src="d.crop_image_url" class="w-8 h-12 object-cover rounded shadow-sm border border-red-300" />
                <div>
                  <div class="text-xs font-bold text-red-900 flex items-center gap-1">
                    <span class="bg-red-500 text-white text-[8px] px-1 rounded">오배열</span> {{ d.ocr_call_number || d.ocr_title }}
                  </div>
                  <div class="text-[10px] text-red-700 mt-0.5">{{ d.ocr_title }}</div>
                </div>
              </div>
              <button class="bg-white text-stone-700 px-2 py-1 rounded border border-stone-300 text-[10px] font-bold shrink-0">조치확인</button>
            </div>

            <div v-else-if="d.status === 'UNKNOWN' || d.status === 'MISSING'" class="bg-orange-50 p-3 rounded-lg border border-orange-200 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <img v-if="d.crop_image_url" :src="d.crop_image_url" class="w-8 h-12 object-cover rounded shadow-sm border border-orange-300" />
                <div>
                  <div class="text-xs font-bold text-orange-900 flex items-center gap-1">
                    <span class="bg-orange-500 text-white text-[8px] px-1 rounded">확인요망</span> {{ d.ocr_call_number || '인식불가' }}
                  </div>
                  <div class="text-[10px] text-orange-700 mt-0.5">AI 신뢰도 {{ Math.round(d.confidence * 100) }}%</div>
                </div>
              </div>
              <button @click="showEditModal = true" class="bg-stone-800 text-white px-3 py-1 rounded text-[10px] font-bold shadow shrink-0">수동교정</button>
            </div>
          </template>
        </div>
      </div>

      <div class="absolute bottom-0 w-full bg-white border-t border-stone-200 p-3 flex gap-2">
        <button class="flex-1 bg-stone-100 text-stone-700 text-xs font-bold py-3 rounded-xl">임시 저장</button>
        <button @click="router.push('/history')" class="flex-[2] bg-[#2E7D32] text-white text-xs font-bold py-3 rounded-xl">조치 완료 및 반영</button>
      </div>

      <!-- Edit Modal -->
      <div v-if="showEditModal" class="absolute inset-0 bg-stone-900/60 z-50 flex items-end justify-center">
        <div class="bg-white w-full h-[75%] rounded-t-2xl p-5 flex flex-col animate-slide-up">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-sm font-extrabold">청구기호 수동 교정</h2>
            <button @click="showEditModal = false" class="text-stone-400 text-xl">✕</button>
          </div>
          <div class="bg-stone-200 h-24 rounded-xl flex items-center justify-center mb-4 relative">
            <div class="bg-orange-500/20 border-2 border-orange-500 w-12 h-16 z-10 flex items-center justify-center font-bold text-orange-800 text-[10px] text-center p-1 bg-white/80">
              81?.*<br>?가
            </div>
          </div>
          <label class="block text-xs font-bold text-stone-600 mb-2">올바른 청구기호 입력</label>
          <input type="text" value="813.6 김15가" class="w-full bg-stone-50 border border-stone-300 rounded-xl px-4 py-3 font-bold text-sm mb-4">
          <button class="w-full bg-stone-100 text-stone-700 py-3 rounded-xl text-xs font-bold border border-stone-200 mb-2">🔍 바코드 매칭</button>
          <button @click="showEditModal = false" class="mt-auto w-full bg-stone-800 text-white font-bold py-4 rounded-xl">저장하기</button>
        </div>
      </div>
    </template>
  </main>
</template>
