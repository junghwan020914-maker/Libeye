<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { SHELF_ROWS, SECTION_LABELS, SHELF_LEVELS } from '../../constants/shelf';

const props = defineProps<{ locations: any }>();
const emit = defineEmits<{ (e: 'select', locationId: string): void }>();

const router = useRouter();

// 💡 1. 3단계 토글 제어를 위한 상태 변수 선언
const currentRow = ref<number | null>(null);     // 선택한 행 (1 ~ 32)
const currentSection = ref<string | null>(null); // 선택한 열 (A ~ G)
const currentLevel = ref<number | null>(null);   // 선택한 단 (5 ~ 1)

// 💡 2. 1~32행 루프 생성 (시각적으로 정돈되도록 1부터 32까지 생성)
const availableRows = SHELF_ROWS;

// 💡 3. A~G열 목록 선언
const availableSections = SECTION_LABELS;

// 💡 4. 5단부터 1단까지 역순 배치 (위 -> 아래 사상 반영)
const levels = SHELF_LEVELS;

// 💡 5. 최종 3단계(단수)까지 터치했을 때 실행되는 매칭 및 카메라 가동 로직
const handleFinalSelect = (row: number, section: string, level: number) => {
  currentRow.value = row;
  currentSection.value = section;
  currentLevel.value = level;

  // 알파벳 가공 ('A열' -> 'A')
  const cleanSection = section.replace('열', '');

  // 데이터베이스 마스터 배열에서 행(shelf_num), 열(section), 단(level_num)이 일치하는 ID 탐색
  const matched = props.locations.find(
    (loc: any) => Number(loc.shelf_num) === row &&
           loc.section.replace('열', '') === cleanSection &&
           Number(loc.level_num) === level
  );

  if (matched) {
    // 🎯 일치하는 실존 구역 발견 시 즉시 세션 연동 및 카메라 View 구동 (확인창 생략)
    emit('select', matched.location_id);
  } else {
    // 💡 실제 DB 세팅이 안 된 더미 구역 클릭 시 부드러운 예외 가이드 알림 후 리셋
    alert(`[안내] 선택하신 ${row}행 ${section} ${level}단은 데모용 더미 구역입니다. 촬영을 원하시면 실제 등록된 A열 또는 B열의 구역을 선택해 주세요.`);
    currentLevel.value = null;
  }
};
</script>

<template>
  <div class="absolute inset-0 z-[60] bg-stone-900 flex flex-col p-5 animate-fade-in select-none">
    <div class="flex justify-between items-center mb-4">
      <button @click="router.push('/')" class="text-white text-2xl active:opacity-60">◀</button>
      <h2 class="text-white text-lg font-bold tracking-tight">점검 위치 지정 (3단계 토글)</h2>
      <div class="w-6"></div>
    </div>

    <div class="flex-1 flex gap-3 overflow-hidden min-h-0 text-xs">

      <div class="w-[28%] flex flex-col bg-stone-950/40 p-2 rounded-xl border border-stone-850">
        <div class="text-stone-400 font-extrabold text-[10px] tracking-wider mb-2 text-center border-b border-stone-800 pb-1">
          1. 행 선택 (번)
        </div>
        <div class="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-0.5">
          <button
            v-for="row in availableRows"
            :key="row"
            @click="() => { currentRow = row; currentSection = null; currentLevel = null; }"
            :class="[
              'py-3 rounded-lg text-center font-bold transition-all border',
              currentRow === row
                ? 'bg-green-600 text-white border-green-500 shadow-sm'
                : 'bg-stone-800 text-stone-400 border-stone-750 active:bg-stone-700'
            ]"
          >
            {{ row }}번 서가
          </button>
        </div>
      </div>

      <div class="w-[32%] flex flex-col bg-stone-950/40 p-2 rounded-xl border border-stone-850">
        <div class="text-stone-400 font-extrabold text-[10px] tracking-wider mb-2 text-center border-b border-stone-800 pb-1">
          2. 열 선택 (열)
        </div>

        <div v-if="!currentRow" class="flex-1 flex items-center justify-center text-stone-600 text-center px-2">
          먼저 좌측에서<br>행을 고르세요
        </div>

        <div v-else class="flex-1 overflow-y-auto flex flex-col gap-1.5 pr-0.5">
          <button
            v-for="section in availableSections"
            :key="section"
            @click="() => { currentSection = section; currentLevel = null; }"
            :class="[
              'py-3.5 rounded-lg text-center font-black text-sm transition-all border',
              currentSection === section
                ? 'bg-green-600 text-white border-green-500'
                : 'bg-stone-800 text-stone-300 border-stone-750 active:bg-stone-700'
            ]"
          >
            {{ section }}
          </button>
        </div>
      </div>

      <div class="flex-1 flex flex-col bg-stone-950/40 p-2 rounded-xl border border-stone-850">
        <div class="text-stone-400 font-extrabold text-[10px] tracking-wider mb-2 text-center border-b border-stone-800 pb-1">
          3. 서가 칸(단) 지정
        </div>

        <div v-if="!currentSection" class="flex-1 flex items-center justify-center text-stone-600 text-center px-4">
          행과 열을<br>모두 지정해주세요
        </div>

        <div v-else class="flex-1 flex flex-col gap-2 justify-between">
          <button
            v-for="level in levels"
            :key="level"
            @click="handleFinalSelect(currentRow!, currentSection!, level)"
            class="flex-1 bg-stone-800 hover:bg-stone-750 border border-stone-700 rounded-lg flex flex-col items-center justify-center p-1 active:bg-stone-600 transition-all text-center group"
          >
            <span class="text-white font-extrabold text-xs group-active:text-green-400">
              {{ level }}단
            </span>
            <span class="text-[9px] text-green-500 font-medium tracking-tighter mt-0.5 opacity-80">
              📸 촬영시작
            </span>
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* 💡 화면이 파랗게 반전되는 드래그 부작용 방지용 스타일 추가 */
main, img, div {
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  -webkit-user-drag: none;
}
</style>