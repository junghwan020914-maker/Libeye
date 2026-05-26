<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<template>
  <main class="flex-col h-full bg-stone-50 relative flex animate-fade-in">
    <header class="bg-white px-4 py-3 border-b border-stone-200 flex items-center shrink-0 sticky top-0 z-20">
      <button @click="router.back()" class="p-2 text-stone-600 text-xl font-bold mr-2 active:scale-90 transition-transform">◀</button>
      <div>
        <h1 class="text-base font-extrabold text-stone-900">촬영 가이드</h1>
        <p class="text-[10px] font-medium text-stone-500">정확도를 90% 이상 올리는 비법</p>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto p-5 pb-28 flex flex-col gap-6">
      
      <section class="flex flex-col gap-4">
        
        <div>
          <h3 class="font-bold text-stone-900 text-[14px] mb-2 flex items-center gap-1">
            <span class="text-emerald-500 text-lg">✅</span> 이렇게 찍어주세요
          </h3>
          <div class="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
            <div class="h-40 bg-stone-800 relative flex items-center justify-center">
              <div class="absolute inset-4 border-2 border-emerald-400/80 bg-emerald-400/10">
                <div class="absolute top-1/3 w-full border-t border-emerald-400/40 border-dashed"></div>
                <div class="absolute top-2/3 w-full border-t border-emerald-400/40 border-dashed"></div>
              </div>
              
              <div class="flex items-end h-28 gap-1 z-10">
                <div class="w-8 h-[95%] bg-stone-300 rounded-sm border-l-4 border-stone-400"></div>
                <div class="w-7 h-full bg-stone-200 rounded-sm border-l-4 border-stone-300"></div>
                <div class="w-9 h-[90%] bg-stone-300 rounded-sm border-l-4 border-stone-400"></div>
                <div class="w-8 h-[98%] bg-stone-200 rounded-sm border-l-4 border-stone-300"></div>
                <div class="w-7 h-[85%] bg-stone-400 rounded-sm border-l-4 border-stone-500"></div>
              </div>
              
              <div class="absolute bottom-2 right-2 bg-emerald-500 text-white text-[10px] font-bold px-2 py-1 rounded shadow-md">
                좋은 예시 O
              </div>
            </div>
            <div class="p-2.5 bg-emerald-50 border-t border-emerald-100">
              <p class="text-[11px] text-emerald-800 font-medium text-center">
                책등이 화면 중앙 격자선과 수평·수직을 이루도록 정면에서 촬영
              </p>
            </div>
          </div>
        </div>

        <div>
          <h3 class="font-bold text-stone-900 text-[14px] mb-2 flex items-center gap-1">
            <span class="text-rose-500 text-lg">❌</span> 이렇게 찍으면 안돼요
          </h3>
          <div class="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
            <div class="h-40 bg-stone-800 relative flex items-center justify-center overflow-hidden">
              <div class="absolute inset-4 border-2 border-rose-500/80 bg-rose-500/10">
                <div class="absolute top-1/3 w-full border-t border-rose-500/40 border-dashed"></div>
                <div class="absolute top-2/3 w-full border-t border-rose-500/40 border-dashed"></div>
              </div>
              
              <div class="flex items-end h-28 gap-1 z-10 rotate-[14deg] scale-75 translate-y-3 translate-x-4">
                <div class="w-8 h-[95%] bg-stone-300 rounded-sm border-l-4 border-stone-400"></div>
                <div class="w-7 h-full bg-stone-200 rounded-sm border-l-4 border-stone-300"></div>
                <div class="w-9 h-[90%] bg-stone-300 rounded-sm border-l-4 border-stone-400"></div>
                <div class="w-8 h-[98%] bg-stone-200 rounded-sm border-l-4 border-stone-300"></div>
                <div class="w-7 h-[85%] bg-stone-400 rounded-sm border-l-4 border-stone-500"></div>
              </div>
              
              <div class="absolute bottom-2 right-2 bg-rose-500 text-white text-[10px] font-bold px-2 py-1 rounded shadow-md">
                나쁜 예시 X
              </div>
            </div>
            <div class="p-2.5 bg-rose-50 border-t border-rose-100">
              <p class="text-[11px] text-rose-800 font-medium text-center">
                스마트폰이 기울어지거나 너무 멀리서 찍어 여백이 많은 상태
              </p>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 class="font-bold text-stone-900 text-[15px] mb-3 mt-2">💡 필수 체크리스트</h3>
        <ul class="flex flex-col gap-3">
          <li class="flex items-start gap-3 bg-white p-3.5 rounded-xl border border-stone-100 shadow-sm">
            <div class="w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5">1</div>
            <p class="text-xs text-stone-700 leading-snug">
              <span class="font-bold text-stone-900 block mb-0.5">권장 수량 (1칸 분량)</span> 
              사진 1장 당 <strong class="text-blue-600">15권~20권 내외</strong>가 포함되게 찍어주세요. 
            </p>
          </li>
          <li class="flex items-start gap-3 bg-white p-3.5 rounded-xl border border-stone-100 shadow-sm">
            <div class="w-5 h-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5">2</div>
            <p class="text-xs text-stone-700 leading-snug">
              <span class="font-bold text-stone-900 block mb-0.5">조명 및 난반사 주의</span> 
              조명이 책등 코팅에 반사되어 글자가 하얗게 날아가지 않도록 주의하세요.
            </p>
          </li>
          <li class="flex items-start gap-3 bg-white p-3.5 rounded-xl border border-stone-100 shadow-sm">
            <div class="w-5 h-5 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5">3</div>
            <p class="text-xs text-stone-700 leading-snug">
              <span class="font-bold text-stone-900 block mb-0.5">초점(흔들림) 확인</span> 
              카메라 초점이 맞을 때까지 1초 정도 기다린 후 촬영하세요.
            </p>
          </li>
        </ul>
      </section>
    </div>

    <div class="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-stone-50 via-stone-50 to-transparent z-20">
      <button 
        @click="router.push('/camera')" 
        class="w-full bg-stone-900 hover:bg-stone-800 text-white font-bold py-4 rounded-xl shadow-[0_4px_14px_0_rgba(0,0,0,0.25)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 text-sm"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        스캔 시작하기
      </button>
    </div>
  </main>
</template>
