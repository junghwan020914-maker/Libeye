<script setup lang="ts">
const props = defineProps<{ group: any; mapStatus: any }>();
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'select-level', loc: any): void;
}>();

const getLevelColor = (locId: string) => {
  const s = props.mapStatus[locId]?.status;
  if (s === 'done') return 'bg-[#2E7D32] text-white';
  if (s === 'error') return 'bg-[#D32F2F] text-white ring-2 ring-red-500/20';
  return 'bg-stone-200 border border-stone-300 text-stone-500';
};
</script>

<template>
  <div class="absolute inset-0 bg-stone-900/60 z-40 flex flex-col justify-end p-0 backdrop-blur-sm transition-all duration-300" @click.self="emit('close')">
    <div class="bg-white w-full rounded-t-3xl p-6 shadow-2xl animate-slide-up flex flex-col max-h-[65vh] mb-20">

      <div class="flex justify-between items-center mb-5 shrink-0">
        <h2 class="text-xl font-extrabold text-stone-900">{{ group?.section }}열 {{ group?.shelf_num }}번 책장</h2>
        <button @click="emit('close')" class="w-8 h-8 bg-stone-100 rounded-full text-stone-600 font-bold hover:bg-stone-200">✕</button>
      </div>

      <p class="text-xs text-stone-500 mb-4 shrink-0">작업할 단(층)을 선택해주세요.</p>

      <div class="flex flex-col-reverse gap-3 overflow-y-auto pb-4 custom-scrollbar">
        <button v-for="loc in group?.levels" :key="loc.location_id"
                @click="emit('select-level', loc)"
                class="p-4 rounded-xl flex items-center justify-between font-bold text-sm shadow-sm transition-transform active:scale-95"
                :class="getLevelColor(loc.location_id)">
          <span>{{ loc.level_num }}단</span>
          <span v-if="mapStatus[loc.location_id]?.status === 'error'" class="text-lg">⚠</span>
          <span v-else-if="mapStatus[loc.location_id]?.status === 'done'" class="text-lg">✅</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slide-up {
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideUp {
  0% { transform: translateY(100%); }
  100% { transform: translateY(0); }
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
