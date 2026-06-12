<script setup lang="ts">
import { usePolygonOverlay } from '../../composables/usePolygonOverlay';

defineProps<{ images?: any; detections?: any }>();

// --- 이미지 스케일 계산 + polygon 좌표 변환 (composable로 분리) ---
const { onImageLoad, getPolygonPoints, getPolygonLabelPos } = usePolygonOverlay();
</script>

<template>
  <div
    class="h-48 bg-stone-300 relative flex overflow-x-auto overflow-y-hidden snap-x shrink-0 shadow-inner scrollbar-hide">

    <div v-if="!images || images.length === 0"
      class="absolute inset-0 flex justify-center items-center opacity-30 text-5xl w-full">📚📚📚</div>

    <div v-for="img in images" :key="img.image_id"
      class="relative h-full min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center border-r-2 border-stone-800/40">

      <img :src="img.image_url" @load="(e) => onImageLoad(e, img.image_id)"
        class="absolute inset-0 w-full h-full object-contain opacity-50" />

      <!-- SVG polygon 오버레이 -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none z-10">
        <template v-for="d in detections" :key="d.detection_id">
          <polygon
            v-if="d.source_image_id === img.image_id && d.status !== 'MATCH' && getPolygonPoints(d, img.image_id)"
            :points="getPolygonPoints(d, img.image_id)" stroke-width="2"
            :stroke="d.status === 'MATCH' ? '#2E7D32' : d.status === 'MISPLACED' ? '#D32F2F' : '#F57C00'"
            :fill="d.status === 'MATCH' ? 'rgba(34,197,94,0.1)' : d.status === 'MISPLACED' ? 'rgba(211,47,47,0.3)' : 'rgba(245,124,0,0.3)'" />
        </template>
      </svg>

      <!-- 배지 레이어 (순서 번호 + 상태 텍스트) -->
      <template v-for="d in detections" :key="`badge-${d.detection_id}`">
        <template
          v-if="d.source_image_id === img.image_id && d.status !== 'MATCH' && getPolygonLabelPos(d, img.image_id)">
          <span
            class="absolute text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full font-bold shadow-md z-20"
            :class="(d.status === 'MISPLACED' && d.is_verified) ? 'bg-[#2E7D32]' : 'bg-stone-800'"
            :style="{
              left: `${getPolygonLabelPos(d, img.image_id)!.x}px`,
              top: `${getPolygonLabelPos(d, img.image_id)!.y - 24}px`
            }">
            {{ d.detected_order }}
          </span>
          <span v-if="d.status !== 'MATCH'"
            class="absolute bg-white border text-[8px] px-1 rounded whitespace-nowrap z-20" :style="{
              left: `${getPolygonLabelPos(d, img.image_id)!.x + 24}px`,
              top: `${getPolygonLabelPos(d, img.image_id)!.y - 20}px`
            }" :class="{
              'border-[#2E7D32] text-[#2E7D32]': d.status === 'MISPLACED' && d.is_verified,
              'border-[#D32F2F] text-[#D32F2F]': d.status === 'MISPLACED' && !d.is_verified,
              'border-[#F57C00] text-[#F57C00]': d.status === 'UNKNOWN' || d.status === 'MISSING'
            }">
            {{ d.status === 'MISPLACED' && d.is_verified ? '제자리-조치완료' : d.status === 'MISPLACED' ?
              '오배열' : '확인요망' }}
          </span>
        </template>
      </template>
    </div>
  </div>
</template>
