<script setup lang="ts">
defineProps<{ items: any }>();
const emit = defineEmits<{ (e: 'select', item: any): void }>();
</script>

<template>
  <section>
    <h3 class="text-xs font-bold text-stone-500 mb-3 ml-1 flex items-center justify-between">
      <span>본 서가 등록 도서 목록</span>
      <span class="bg-stone-300 text-stone-700 px-2 py-0.5 rounded-full text-[9px]">
        총 {{ items.length }}권
      </span>
    </h3>
    <div class="flex flex-col gap-2">
      <template v-for="item in items" :key="item.book_id">

        <div v-if="item.status === 'MATCH'" @click="emit('select', item)"
          class="bg-white p-3 rounded-lg border border-stone-200 flex items-center justify-between cursor-pointer hover:bg-stone-50 transition-colors shadow-sm">
          <div class="flex items-center gap-3">
            <img v-if="item.detection?.crop_image_url" :src="item.detection.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border border-stone-200 bg-stone-100" />
            <div v-else
              class="w-8 h-12 bg-stone-100 rounded border border-stone-200 flex items-center justify-center text-[10px] text-stone-400">
              정상</div>
            <div>
              <div class="text-xs font-bold text-stone-800">{{ item.call_number }}</div>
              <div class="text-[10px] text-stone-500 mt-0.5 w-48 truncate">{{ item.title }}
              </div>
            </div>
          </div>
          <span
            class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">제자리</span>
        </div>


        <div v-else-if="item.status === 'DUPLICATE'" @click="emit('select', item)"
          class="p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-colors shadow-sm"
          :class="item.detection?.is_verified ? 'bg-white border-stone-200 hover:bg-stone-50' : 'border-2 bg-red-50 border-red-300 hover:bg-red-100'">

          <div class="flex items-center gap-3">
            <img v-if="item.detection?.crop_image_url" :src="item.detection.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border"
              :class="item.detection?.is_verified ? 'border-stone-200 bg-stone-100' : 'border-red-300'" />
            <div v-else
              class="w-8 h-12 rounded border flex items-center justify-center text-[10px]"
              :class="item.detection?.is_verified ? 'bg-stone-100 border-stone-200 text-stone-400' : 'bg-red-100 border-red-300 text-red-400'">
              {{ item.detection?.is_verified ? '정상' : '오류' }}
            </div>

            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="item.detection?.is_verified ? 'text-stone-800' : 'text-red-900'">
                <span v-if="!item.detection?.is_verified"
                  class="bg-red-500 text-white text-[9px] px-1.5 py-0.5 rounded shadow-sm">중복매칭</span>
                {{ item.call_number }}
              </div>
              <div class="text-[10px] mt-0.5 truncate"
                :class="item.detection?.is_verified ? 'text-stone-500 w-48' : 'text-red-700 w-40'">
                {{ item.title }}
              </div>
            </div>
          </div>

          <span v-if="item.detection?.is_verified">
            <span v-if="item.detection?.verification_method === 'BATCH_OVERWRITE'"
              class="text-[10px] font-bold text-stone-600 bg-stone-200 px-2 py-1 rounded">일괄-강제완료</span>
            <span v-else
              class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">제자리-조치완료</span>
          </span>
          <div v-else class="text-right flex flex-col items-end gap-1">
            <span class="text-[10px] text-stone-400">자세히 보기 ❯</span>
          </div>
        </div>



        <div v-else-if="item.status === 'MISPLACED'" @click="emit('select', item)"
          class="p-3 rounded-lg border flex items-center justify-between cursor-pointer transition-colors shadow-sm"
          :class="item.detection?.is_verified ? 'bg-white border-stone-200 hover:bg-stone-50' : 'border-2 bg-red-50 border-red-300 hover:bg-red-100'">

          <div class="flex items-center gap-3">
            <img v-if="item.detection?.crop_image_url" :src="item.detection.crop_image_url"
              class="w-8 h-12 object-cover rounded shadow-sm border"
              :class="item.detection?.is_verified ? 'border-stone-200 bg-stone-100' : 'border-red-300'" />
            <div v-else
              class="w-8 h-12 rounded border flex items-center justify-center text-[10px]"
              :class="item.detection?.is_verified ? 'bg-stone-100 border-stone-200 text-stone-400' : 'bg-red-100 border-red-300 text-red-400'">
              {{ item.detection?.is_verified ? '정상' : '오류' }}</div>

            <div>
              <div class="text-xs font-bold flex items-center gap-1"
                :class="item.detection?.is_verified ? 'text-stone-800' : 'text-red-900'">
                <span v-if="!item.detection?.is_verified"
                  class="bg-red-500 text-white text-[9px] px-1.5 py-0.5 rounded shadow-sm">순서오류</span>
                {{ item.call_number }}
              </div>
              <div class="text-[10px] mt-0.5 truncate"
                :class="item.detection?.is_verified ? 'text-stone-500 w-48' : 'text-red-700 w-40'">
                {{ item.title }}</div>
            </div>
          </div>

          <span v-if="item.detection?.is_verified">
            <span v-if="item.detection?.verification_method === 'BATCH_OVERWRITE'"
              class="text-[10px] font-bold text-stone-600 bg-stone-200 px-2 py-1 rounded">일괄-강제완료</span>
            <span v-else
              class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">제자리-조치완료</span>
          </span>
          <div v-else class="text-right flex flex-col items-end gap-1">
            <span class="text-[10px] text-stone-400">자세히 보기 ❯</span>
          </div>
        </div>

        <div v-else-if="item.status === 'MISSING'"
          class="bg-stone-50 p-3 rounded-lg border border-dashed border-stone-400 flex items-center justify-between opacity-80">
          <div class="flex items-center gap-3">
            <div
              class="w-8 h-12 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-[12px] font-bold text-stone-500 opacity-60">
              ?</div>
            <div>
              <div class="text-xs font-bold text-stone-600 flex items-center gap-1">
                <span class="bg-stone-600 text-white text-[8px] px-1 rounded">유실/미인식</span>
                {{ item.call_number }}
              </div>
              <div class="text-[10px] text-stone-500 mt-0.5 w-48 truncate">{{ item.title }}
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
