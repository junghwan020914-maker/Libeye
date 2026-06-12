<script setup lang="ts">
defineProps<{ data: { title: string; status: string; content: string } }>();
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'go-history'): void;
  (e: 'go-camera'): void;
}>();
</script>

<template>
  <div class="absolute inset-0 bg-stone-900/60 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
    <div class="bg-white w-full max-w-sm rounded-2xl p-5 shadow-2xl animate-pop-in">
      <div class="flex justify-between items-start mb-3">
        <div>
          <h2 class="text-lg font-extrabold text-stone-900">{{ data.title }}</h2>
        </div>
        <button @click="emit('close')" class="w-6 h-6 bg-stone-100 hover:bg-stone-200 rounded-full text-stone-600 font-bold flex items-center justify-center">✕</button>
      </div>
      <div class="mb-5 text-sm rounded-xl p-4"
           :class="{
             'bg-red-50 border border-red-200': data.status === 'error',
             'bg-green-50 border border-green-200': data.status === 'done',
             'bg-stone-100 border border-stone-200': data.status === 'pending'
           }"
           v-html="data.content"></div>
      <div class="flex gap-3">
        <button @click="emit('go-history')"
                class="flex-1 bg-white border border-stone-300 text-stone-700 text-sm font-bold py-3.5 rounded-xl transition-colors hover:bg-stone-50 shadow-sm">
          최근 기록 보기
        </button>
        <button @click="emit('go-camera')"
                class="flex-1 bg-stone-800 text-white text-sm font-bold py-3.5 rounded-xl transition-colors hover:bg-stone-700 shadow-sm">
          스캔하기
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-pop-in {
  animation: popIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes popIn {
  0% { opacity: 0; transform: scale(0.95); }
  100% { opacity: 1; transform: scale(1); }
}
</style>
