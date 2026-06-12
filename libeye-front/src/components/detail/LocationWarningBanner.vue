<script setup lang="ts">
defineProps<{ warning: any }>();
</script>

<template>
  <div class="bg-amber-50 border-b border-amber-300 px-4 py-2.5 flex items-start gap-2 shrink-0">
    <span class="text-amber-500 text-base leading-none mt-0.5">⚠</span>
    <div class="text-xs text-amber-800 leading-snug">
      <span class="font-bold">서가 불일치 감지</span><br />
      선택한 서가(<span class="font-mono font-semibold">{{ warning.selected_location_id
      }}</span>)와
      실제 스캔된 책들의 서가(<span class="font-mono font-semibold">{{
        warning.actual_location_id }}</span>)가 다릅니다.
      올바른 서가를 선택하고 다시 스캔해주세요.
    </div>
  </div>
</template>
