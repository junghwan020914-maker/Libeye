<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { startSession, getLocations } from '../api/sessionAPI';
import { useCameraStream } from '../composables/useCameraStream';
import { useCropBox } from '../composables/useCropBox';
import { dataURLtoFile } from '../utils/file';
import { enterFullScreen, exitFullScreen } from '../utils/fullscreen';
import LocationSelectModal from '../components/camera/LocationSelectModal.vue';
import CameraTopBar from '../components/camera/CameraTopBar.vue';
import CameraGridGuide from '../components/camera/CameraGridGuide.vue';
import CropBoxOverlay from '../components/camera/CropBoxOverlay.vue';
import CameraErrorPanel from '../components/camera/CameraErrorPanel.vue';
import CameraBottomBar from '../components/camera/CameraBottomBar.vue';
import CaptureConfirmSheet from '../components/camera/CaptureConfirmSheet.vue';
import UploadingOverlay from '../components/camera/UploadingOverlay.vue';
import { dataURLtoFile, blobToFile } from '../utils/file';

const router = useRouter();
const route = useRoute();
const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const previewUrl = ref<string | null>(null);
const isUploading = ref(false);

// Location State
const locations = ref<any[]>([]);
const selectedLocation = ref<string | null>(null);
const showLocationModal = ref(true);

// 카메라 스트림 제어 (composable로 분리)
const { isCameraError, startCamera, stopCamera } = useCameraStream(videoRef, selectedLocation);

// 기존 래퍼용 구역 선택 함수 (startCamera 연동 유지)
const selectLocation = (locationId: string) => {
  selectedLocation.value = locationId;
  showLocationModal.value = false;
  startCamera();
};

// Crop & Upload State
const isCropping = ref(false);
const uploadedImage = ref<HTMLImageElement | null>(null);

// 다중 촬영용 상태
const capturedFiles = ref<File[]>([]);
const capturedPreviews = ref<string[]>([]);
const isConfirming = ref(false);

const fileInputRef = ref<HTMLInputElement | null>(null);
const imageContainerRef = ref<HTMLDivElement | null>(null);

// 💡 크롭박스 상태 + 드래그/리사이즈 제어 (composable로 분리)
const { cropBox, hasCropBox, cropRect, startCropDrag, moveCropDrag, endCropDrag } = useCropBox(imageContainerRef);

const takePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return;

  const video = videoRef.value;
  const canvas = canvasRef.value;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.drawImage(video, 0, 0);
  canvas.toBlob((blob) => {
    if (!blob) {
      alert('이미지 추출에 실패했습니다.');
      return;
    }
    
    stopCamera();

    const file = blobToFile(blob, `camera_${Date.now()}.png`);
    // 프리뷰(미리보기)를 위해 Object URL 생성 (메모리 효율적)
    const previewUrlStr = URL.createObjectURL(blob);

    capturedFiles.value.push(file);
    capturedPreviews.value.push(previewUrlStr);

    isConfirming.value = true;
  }, 'image/png');
};

const triggerFileUpload = () => {
  if (fileInputRef.value) fileInputRef.value.click();
};

const handleFileUpload = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || target.files.length === 0) return;

  const file = target.files[0];
  const reader = new FileReader();
  reader.onload = (ev) => {
    stopCamera();
    previewUrl.value = ev.target?.result as string;
    isCropping.value = true;
    hasCropBox.value = true; // 기본 가이드라인 박스 활성화

    const img = new Image();
    img.onload = () => {
      uploadedImage.value = img;
      if (imageContainerRef.value) {
        const cw = imageContainerRef.value.clientWidth;
        const ch = imageContainerRef.value.clientHeight;
        // 처음에 적당히 중앙에 크롭 가이드라인 배치
        cropBox.value = {
          x1: cw * 0.1,
          y1: ch * 0.2,
          x2: cw * 0.9,
          y2: ch * 0.8
        };
      }
    };
    img.src = previewUrl.value as string;
  };
  reader.readAsDataURL(file);
};

const applyCropAndUpload = async () => {
  if (!uploadedImage.value || !canvasRef.value || !imageContainerRef.value || !hasCropBox.value) return;

  const canvas = canvasRef.value;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const container = imageContainerRef.value;
  const imgRatio = uploadedImage.value.width / uploadedImage.value.height;
  const contRatio = container.clientWidth / container.clientHeight;

  let drawW, drawH, offsetX, offsetY;

  if (imgRatio > contRatio) {
    drawW = container.clientWidth;
    drawH = drawW / imgRatio;
    offsetX = 0;
    offsetY = (container.clientHeight - drawH) / 2;
  } else {
    drawH = container.clientHeight;
    drawW = drawH * imgRatio;
    offsetX = (container.clientWidth - drawW) / 2;
    offsetY = 0;
  }

  const { x, y, w, h } = cropRect.value;
  const ix = Math.max(x, offsetX);
  const iy = Math.max(y, offsetY);
  const iw = Math.min(x + w, offsetX + drawW) - ix;
  const ih = Math.min(y + h, offsetY + drawH) - iy;

  if (iw <= 0 || ih <= 0) {
    alert('크롭 영역이 올바르지 않습니다.');
    return;
  }

  const scaleX = uploadedImage.value.width / drawW;
  const scaleY = uploadedImage.value.height / drawH;

  const sourceX = Math.max(0, (ix - offsetX) * scaleX);
  const sourceY = Math.max(0, (iy - offsetY) * scaleY);
  const sourceW = Math.max(1, iw * scaleX);
  const sourceH = Math.max(1, ih * scaleY);

  canvas.width = Math.floor(sourceW);
  canvas.height = Math.floor(sourceH);

  ctx.drawImage(uploadedImage.value, sourceX, sourceY, sourceW, sourceH, 0, 0, canvas.width, canvas.height);
  canvas.toBlob((blob) => {
    if (!blob) {
      alert('이미지 크롭에 실패했습니다.');
      return;
    }

    const file = blobToFile(blob, `crop_${Date.now()}.png`);
    const croppedPreviewUrl = URL.createObjectURL(blob);

    capturedFiles.value.push(file);
    capturedPreviews.value.push(croppedPreviewUrl);

    isCropping.value = false;
    previewUrl.value = null;
    isConfirming.value = true;
  }, 'image/png');
};

// 크롭 취소 (기존 인라인 핸들러를 메서드로 분리)
const cancelCrop = () => {
  isCropping.value = false;
  previewUrl.value = null;
  startCamera();
};

const takeAnother = () => {
  isConfirming.value = false;
  previewUrl.value = null;
  startCamera();
};

const removeCaptured = (index: number) => {
  capturedFiles.value.splice(index, 1);
  capturedPreviews.value.splice(index, 1);
  if (capturedFiles.value.length === 0) {
    takeAnother();
  }
};

const uploadAll = async () => {
  if (capturedFiles.value.length === 0) return;

  isUploading.value = true;
  try {
    const response = await startSession(selectedLocation.value || 'UNKNOWN', capturedFiles.value);
    capturedFiles.value = [];
    capturedPreviews.value = [];
    router.push({ name: 'detail', query: { sessionId: response.session_id } });
  } catch (err) {
    console.error('Upload error:', err);
    alert('업로드 중 오류가 발생했습니다.');
  } finally {
    isUploading.value = false;
  }
};

const simulateCapture = async () => {
  isUploading.value = true;
  try {
    const dummyDataUrl = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=";
    const file = dataURLtoFile(dummyDataUrl, 'dummy.png');

    const response = await startSession(selectedLocation.value || 'UNKNOWN', [file]);
    router.push({ name: 'detail', query: { sessionId: response.session_id } });
  } catch (err) {
    console.error('Upload error:', err);
    alert('업로드 중 오류가 발생했습니다.');
    isUploading.value = false;
  }
};

onMounted(async () => {
  document.body.classList.add('camera-mode');
  enterFullScreen();

  try {
    locations.value = await getLocations();
    const queryLocationId = route.query.locationId;

    if (queryLocationId) {
      const matchedLoc = locations.value.find((loc: any) => loc.location_id === queryLocationId);
      if (matchedLoc) {
        selectedLocation.value = matchedLoc.location_id;
        showLocationModal.value = false;
      }
    }
  } catch (err) {
    console.error("Failed to load locations", err);
  }
});

onBeforeUnmount(() => {
  document.body.classList.remove('camera-mode');
  exitFullScreen();
  stopCamera();
});
</script>

<template>
  <main class="flex-col h-full bg-black relative z-30 flex animate-fade-in select-none">
    <LocationSelectModal v-if="showLocationModal" :locations="locations"
      @select="(id: string) => { selectedLocation = id; showLocationModal = false; startCamera(); }" />

    <CameraTopBar :selected-location="selectedLocation" :is-cropping="isCropping" />

    <div
      ref="imageContainerRef"
      class="flex-1 relative overflow-hidden flex items-center justify-center bg-stone-800 touch-none select-none"
      @mousedown="isCropping ? startCropDrag($event) : null"
      @mousemove="isCropping ? moveCropDrag($event) : null"
      @mouseup="isCropping ? endCropDrag() : null"
      @mouseleave="isCropping ? endCropDrag() : null"
      @touchstart="isCropping ? startCropDrag($event) : null"
      @touchmove="isCropping ? moveCropDrag($event) : null"
      @touchend="isCropping ? endCropDrag() : null"
    >
      <video v-show="!previewUrl && !isCameraError" ref="videoRef" autoplay playsinline class="absolute w-full h-full object-cover"></video>
      <canvas ref="canvasRef" class="hidden"></canvas>
      <img v-if="previewUrl" :src="previewUrl" class="absolute w-full h-full object-contain pointer-events-none z-10 select-none" draggable="false" />

      <CameraGridGuide v-if="!previewUrl && !isCameraError" />

      <CropBoxOverlay v-if="isCropping && hasCropBox && cropRect.w > 0" :rect="cropRect" />

      <CameraErrorPanel v-if="isCameraError && !isCropping" @simulate="simulateCapture" />
    </div>

    <input type="file" ref="fileInputRef" accept="image/*" class="hidden" @change="handleFileUpload" />

    <CameraBottomBar :is-cropping="isCropping" :is-uploading="isUploading" :is-camera-error="isCameraError"
      @gallery="triggerFileUpload" @shutter="takePhoto" @apply-crop="applyCropAndUpload" @cancel-crop="cancelCrop" />

    <CaptureConfirmSheet v-if="isConfirming" :previews="capturedPreviews" :count="capturedFiles.length"
      :is-uploading="isUploading" @remove="removeCaptured" @take-another="takeAnother" @upload-all="uploadAll" />

    <UploadingOverlay v-if="isUploading" />
  </main>
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
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
