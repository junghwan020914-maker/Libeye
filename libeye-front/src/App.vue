<script setup lang="ts">
import DirectUploader from './components/uploader/DirectUploader.vue';
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
    <header class="mb-8 text-center">
      <h1 class="text-3xl font-extrabold text-gray-900 tracking-tight">Vision AI 서가 관리</h1>
      <p class="text-gray-500 mt-2">WebAR 도서 내비게이션 시스템</p>
    </header>

    <main class="w-full max-w-md">
      <DirectUploader />
    </main>
  </div>
</template>
