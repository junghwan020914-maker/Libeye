<template>
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
</template>
