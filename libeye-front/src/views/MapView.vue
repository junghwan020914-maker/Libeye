<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const showModal = ref(false);
const modalData = ref({ title: '', status: '', content: '' });

const showShelfModal = (id: string, status: string) => {
  modalData.value.title = `${id} 서가`;
  modalData.value.status = status;
  
  if (status === 'error') {
    modalData.value.content = `<div class="font-bold text-red-800 mb-1">⚠ 조치 필요</div><ul class="text-red-700"><li>• 오배열 1건</li><li>• 누락 1건</li></ul>`;
  } else if (status === 'done') {
    modalData.value.content = `<div class="font-bold text-green-800">✅ 점검 완료</div>`;
  } else {
    modalData.value.content = `<div class="font-bold text-stone-800">미점검 상태</div>`;
  }
  
  showModal.value = true;
};

const goToCamera = () => {
  router.push('/camera');
};
</script>

<template>
  <main class="flex-col h-full animate-fade-in pb-20 bg-stone-100 overflow-y-auto flex">
    <header class="bg-white px-5 py-4 border-b border-stone-200 sticky top-0 z-20 shrink-0">
      <h1 class="text-xl font-extrabold text-stone-900">서고 작업 지도</h1>
      <p class="text-xs font-medium text-stone-500">인문과학실 3층 A~D열</p>
    </header>
    <div class="bg-white px-5 py-2 border-b border-stone-100 flex gap-3 text-[9px] font-bold text-stone-600 shrink-0">
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-stone-200 border border-stone-300"></span> 미점검</div>
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#2E7D32]"></span> 정상</div>
      <div class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded bg-[#D32F2F]"></span> 오류 발생</div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 relative">
      <div class="absolute left-6 right-6 top-1/2 h-10 bg-stone-200/50 rounded flex items-center justify-center text-stone-400 font-bold tracking-widest text-xs pointer-events-none">중앙 통로</div>
      
      <div class="grid grid-cols-4 gap-x-3 gap-y-5 mb-20 relative z-10">
        <div @click="showShelfModal('A-1', 'done')" class="h-16 bg-[#2E7D32] rounded flex items-center justify-center text-white font-bold text-xs cursor-pointer active:scale-95 transition-transform">A-1</div>
        <div @click="showShelfModal('A-2', 'error')" class="h-16 bg-[#D32F2F] rounded flex items-center justify-center text-white font-bold text-xs ring-2 ring-red-500/20 cursor-pointer active:scale-95 transition-transform">A-2</div>
        <div @click="showShelfModal('A-3', 'done')" class="h-16 bg-[#2E7D32] rounded flex items-center justify-center text-white font-bold text-xs cursor-pointer active:scale-95 transition-transform">A-3</div>
        <div @click="showShelfModal('A-4', 'pending')" class="h-16 bg-stone-200 border border-stone-300 rounded flex items-center justify-center text-stone-500 font-bold text-xs cursor-pointer active:scale-95 transition-transform">A-4</div>
        
        <div class="h-16 bg-stone-200 border border-stone-300 rounded flex items-center justify-center text-stone-500 font-bold text-xs">B-1</div>
        <div class="h-16 bg-stone-200 border border-stone-300 rounded flex items-center justify-center text-stone-500 font-bold text-xs">B-2</div>
        <div class="h-16 bg-[#D32F2F] rounded flex items-center justify-center text-white font-bold text-xs cursor-pointer active:scale-95 transition-transform">B-3</div>
        <div class="h-16 bg-stone-200 border border-stone-300 rounded flex items-center justify-center text-stone-500 font-bold text-xs">B-4</div>
      </div>
    </div>

    <!-- Map Modal -->
    <div v-if="showModal" class="absolute inset-0 bg-stone-900/40 z-50 flex items-center justify-center p-6 backdrop-blur-sm">
      <div class="bg-white w-full rounded-2xl p-5 shadow-2xl animate-pop-in">
        <div class="flex justify-between items-start mb-3">
          <div>
            <h2 class="text-lg font-extrabold text-stone-900">{{ modalData.title }}</h2>
            <p class="text-[10px] text-stone-500">최근 점검: 14:15</p>
          </div>
          <button @click="showModal = false" class="w-6 h-6 bg-stone-100 rounded-full text-stone-600 font-bold">✕</button>
        </div>
        <div class="mb-4 text-xs rounded-xl p-3" 
             :class="{
               'bg-red-50 border border-red-200': modalData.status === 'error',
               'bg-green-50 border border-green-200': modalData.status === 'done',
               'bg-stone-100 border border-stone-200': modalData.status === 'pending'
             }"
             v-html="modalData.content"></div>
        <button @click="goToCamera" class="w-full bg-stone-800 text-white text-xs font-bold py-3 rounded-xl">이 구역 스캔하기</button>
      </div>
    </div>
  </main>
</template>
