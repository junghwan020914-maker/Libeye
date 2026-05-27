<template>
  <div class="p-6 max-w-lg mx-auto">
    <h1 class="text-2xl font-bold mb-4">북카트 정리 도우미</h1>
    <p class="text-gray-600 mb-6">북카트에 꽂힌 책들의 책등이 잘 보이게 사진을 찍어주세요.</p>

    <div class="border-2 border-dashed border-gray-400 rounded-lg p-10 text-center bg-gray-50">
      <input 
        type="file" 
        accept="image/*" 
        capture="environment"
        @change="handleFileUpload" 
        class="hidden" 
        ref="fileInput" 
      />
      <button 
        @click="triggerFileInput" 
        class="bg-blue-600 text-white px-6 py-3 rounded-lg shadow hover:bg-blue-700 transition"
        :disabled="isUploading"
      >
        {{ isUploading ? '업로드 중...' : '사진 촬영 / 갤러리 선택' }}
      </button>
    </div>
    
    <div v-if="errorMessage" class="mt-4 text-red-500 text-center">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { cartAPI } from '../api/cartAPI';

const router = useRouter();
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);
const errorMessage = ref('');

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  isUploading.value = true;
  errorMessage.value = '';

  try {
    const res = await cartAPI.uploadCartImage(file);
    // 업로드 성공 시 결과 대기 화면으로 이동
    router.push(`/cart-result/${res.session_id}`);
  } catch (error) {
    errorMessage.value = '업로드에 실패했습니다. 다시 시도해주세요.';
    console.error(error);
  } finally {
    isUploading.value = false;
  }
};
</script>