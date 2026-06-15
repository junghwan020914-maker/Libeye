<script setup lang="ts">
defineProps<{ detections: any }>();
const emit = defineEmits<{
  (e: 'select', d: any): void;
  (e: 'edit', d: any): void;
}>();
</script>

<template>
  <section>
    <h3 class="text-xs font-bold text-orange-600 mb-3 ml-1 flex items-center gap-1">
      <span>⚠️ 잘못 꽂힌 타 구역 도서 및 미인식 도서</span>
    </h3>
    <div class="flex flex-col gap-2">
      <template v-for="d in detections" :key="d.detection_id">

        <div v-if="d.status === 'MISPLACED'"
          class="p-3 rounded-lg border flex items-center justify-between shadow-sm transition-colors"
          :class="d.is_verified ? 'bg-white border-stone-200 hover:bg-stone-50' : 'bg-orange-50 border-orange-300'">
          <div class="flex items-center gap-3 cursor-pointer" @click="emit('select', d)">
            <img v-if="d.crop_image_url" :src="d.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border"
              :class="d.is_verified ? 'border-stone-200 bg-stone-100' : 'border-orange-400'" />
            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="d.is_verified ? 'text-stone-800' : 'text-orange-900'">
                <span class="text-white text-[8px] px-1 rounded shadow-sm"
                  :class="d.is_verified ? 'bg-stone-400' : 'bg-orange-500'">외부도서</span>
                {{ d.ocr_call_number || d.ocr_title }}
              </div>
              <div class="text-[10px] mt-1 bg-white inline-block px-2 py-0.5 rounded border"
                :class="d.is_verified ? 'text-stone-500 border-stone-200' : 'text-orange-800 border-orange-200'">
                원래 위치: <strong>{{ d.assigned_loc_id || '알 수 없음' }}</strong>
              </div>
            </div>
          </div>
          
          <div v-if="d.is_verified" class="shrink-0 ml-2">
            <span v-if="d.verification_method === 'BATCH_OVERWRITE'"
              class="text-[10px] font-bold text-stone-600 bg-stone-200 px-2 py-1 rounded">일괄-강제완료</span>
            <span v-else
              class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">조치완료</span>
          </div>
          <button v-else @click.stop="emit('edit', d)"
            class="bg-orange-600 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
        </div>

        <div v-else-if="d.status === 'OCR_FAILED'"
          class="p-3 rounded-lg border flex items-center justify-between shadow-sm transition-colors"
          :class="d.is_verified ? 'bg-white border-stone-200' : 'bg-red-50 border-red-200'">
          <div class="flex items-center gap-3 cursor-pointer" @click="emit('select', d)">
            <img v-if="d.crop_image_url" :src="d.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border"
              :class="d.is_verified ? 'border-stone-200 bg-stone-100' : 'border-red-300'" />
            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="d.is_verified ? 'text-stone-800' : 'text-red-900'">
                <span class="text-white text-[8px] px-1 rounded"
                  :class="d.is_verified ? 'bg-stone-400' : 'bg-red-500'">OCR 실패</span> 
                {{ d.ocr_call_number || d.ocr_title || '텍스트 판독 불가' }}
              </div>
              <div class="text-[10px] mt-1" :class="d.is_verified ? 'text-stone-500' : 'text-red-600'">
                {{ d.is_verified ? '수동 수정을 통해 조치 완료되었습니다.' : 'Gemma 모델이 문자를 인식하지 못했습니다. (재촬영 권장)' }}
              </div>
            </div>
          </div>
          <div v-if="d.is_verified" class="shrink-0 ml-2">
            <span class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">조치완료</span>
          </div>
          <button v-else @click.stop="emit('edit', d)"
            class="bg-stone-800 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
        </div>

        <div v-else-if="d.status === 'MATCH_FAILED'"
          class="p-3 rounded-lg border flex items-center justify-between shadow-sm transition-colors"
          :class="d.is_verified ? 'bg-white border-stone-200' : 'bg-stone-100 border-stone-300'">
          <div class="flex items-center gap-3 cursor-pointer" @click="emit('select', d)">
            <img v-if="d.crop_image_url" :src="d.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border border-stone-300" />
            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="d.is_verified ? 'text-stone-800' : 'text-stone-700'">
                <span class="text-white text-[8px] px-1 rounded"
                  :class="d.is_verified ? 'bg-stone-400' : 'bg-orange-500'">매칭 실패</span> 
                {{ d.ocr_call_number || d.ocr_title || '해독 불가' }}
              </div>
              <div class="text-[10px] text-stone-500 mt-1">
                최고 매칭 점수 <strong>{{ Math.round(d.highest_score) }}점</strong> (도서 정보 부족)
              </div>
            </div>
          </div>
          <div v-if="d.is_verified" class="shrink-0 ml-2">
            <span class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">조치완료</span>
          </div>
          <button v-else @click.stop="emit('edit', d)"
            class="bg-stone-800 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
        </div>

        <div v-else-if="d.status === 'UNKNOWN'"
          class="p-3 rounded-lg border flex items-center justify-between transition-colors"
          :class="d.is_verified ? 'bg-white border-stone-200' : 'bg-stone-100 border-stone-300'">
          <div class="flex items-center gap-3 cursor-pointer" @click="emit('select', d)">
            <img v-if="d.crop_image_url" :src="d.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border border-stone-300" />
            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="d.is_verified ? 'text-stone-800' : 'text-stone-700'">
                <span class="text-white text-[8px] px-1 rounded"
                  :class="d.is_verified ? 'bg-stone-400' : 'bg-stone-500'">미인식</span> 
                {{ d.ocr_call_number || '해독 불가' }}
              </div>
              <div class="text-[10px] text-stone-500 mt-0.5">최고 매칭 점수 {{ Math.round(d.highest_score) }}점</div>
            </div>
          </div>
          <div v-if="d.is_verified" class="shrink-0 ml-2">
            <span class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">조치완료</span>
          </div>
          <button v-else @click.stop="emit('edit', d)"
            class="bg-stone-800 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
        </div>

        <div v-else-if="d.status === 'DUPLICATE'"
          class="p-3 rounded-lg border flex items-center justify-between shadow-sm transition-colors"
          :class="d.is_verified ? 'bg-white border-stone-200' : 'bg-orange-50 border-orange-300'">
          <div class="flex items-center gap-3 cursor-pointer" @click="emit('select', d)">
            <img v-if="d.crop_image_url" :src="d.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border"
              :class="d.is_verified ? 'border-stone-200 bg-stone-100' : 'border-orange-400'" />
            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="d.is_verified ? 'text-stone-800' : 'text-orange-900'">
                <span class="text-white text-[8px] px-1 rounded"
                  :class="d.is_verified ? 'bg-stone-400' : 'bg-red-500'">중복매칭</span>
                {{ d.ocr_call_number || d.ocr_title || '도서명 미상' }}
              </div>
              <div class="text-[10px] mt-1 bg-white inline-block px-2 py-0.5 rounded border"
                :class="d.is_verified ? 'text-stone-500 border-stone-200' : 'text-orange-800 border-orange-200'">
                인식 청구기호: <strong>{{ d.ocr_call_number || '판독불가' }}</strong>
              </div>
            </div>
          </div>
          <div v-if="d.is_verified" class="shrink-0 ml-2">
            <span v-if="d.verification_method === 'BATCH_OVERWRITE'"
              class="text-[10px] font-bold text-stone-600 bg-stone-200 px-2 py-1 rounded">일괄-강제완료</span>
            <span v-else
              class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">조치완료</span>
          </div>
          <button v-else @click.stop="emit('edit', d)"
            class="bg-orange-600 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
        </div>

      </template>
    </div>
  </section>
</template>