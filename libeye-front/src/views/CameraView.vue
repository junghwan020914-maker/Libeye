<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router'; // 💡 useRoute 추가
import { startSession, getLocations } from '../api/sessionAPI';

const router = useRouter();
const route = useRoute(); // 💡 라우트 객체 생성 추가
const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const previewUrl = ref<string | null>(null);
const isCameraReady = ref(false);
const isCameraError = ref(false);
const isUploading = ref(false);
const currentStream = ref<MediaStream | null>(null);

// Location State
const locations = ref<any[]>([]);
const selectedLocation = ref<string | null>(null);
const showLocationModal = ref(true);

const selectLocation = (locationId: string) => {
  selectedLocation.value = locationId;    // 선택된 구역 ID 저장
  showLocationModal.value = false;       // 구역 선택 모달 닫기
  startCamera();                         // 🎥 즉시 카메라 켜기
};

// Crop & Upload State
const isCropping = ref(false);
const uploadedImage = ref<HTMLImageElement | null>(null);
const cropStart = ref({ x: 0, y: 0 });
const cropEnd = ref({ x: 0, y: 0 });
const isDraggingCrop = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const imageContainerRef = ref<HTMLDivElement | null>(null);

// 🚨 기존 상태 변수들 아래에 다중 촬영용 상태 추가
const capturedFiles = ref<File[]>([]);
const capturedPreviews = ref<string[]>([]);
const isConfirming = ref(false); // 촬영 후 확인 창 표시 여부

// Portrait mode check
const isPortrait = ref(window.matchMedia("(orientation: portrait)").matches);
const handleOrientationChange = (e: MediaQueryListEvent) => {
  isPortrait.value = e.matches;
};

const cropRect = computed(() => {
  const x = Math.min(cropStart.value.x, cropEnd.value.x);
  const y = Math.min(cropStart.value.y, cropEnd.value.y);
  const w = Math.abs(cropStart.value.x - cropEnd.value.x);
  const h = Math.abs(cropStart.value.y - cropEnd.value.y);
  return { x, y, w, h };
});

const enterFullScreen = () => {
  const elem = document.documentElement;
  if (elem.requestFullscreen) {
    elem.requestFullscreen().catch(err => {
      console.warn(`Error attempting to enable fullscreen: ${err.message}`);
    });
  }
};

const exitFullScreen = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen().catch(err => {
      console.warn(`Error attempting to disable fullscreen: ${err.message}`);
    });
  }
};

const startCamera = async () => {
  if (!selectedLocation.value) return; // 구역이 선택되어야만 카메라 시작
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
    currentStream.value = stream;
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      isCameraReady.value = true;
    }
  } catch (err) {
    console.error('Camera access error:', err);
    isCameraError.value = true;
  }
};

const stopCamera = () => {
  if (currentStream.value) {
    currentStream.value.getTracks().forEach(t => t.stop());
    currentStream.value = null;
  }
};

// 🚨 기존 getPureBase64 함수 삭제 후 아래 함수로 교체
const dataURLtoFile = (dataurl: string, filename: string): File => {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
};

const takePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return;
  
  const video = videoRef.value;
  const canvas = canvasRef.value;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  ctx.drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
  
  stopCamera();
  
  // File 객체로 변환하여 배열에 누적
  const file = dataURLtoFile(dataUrl, `camera_${Date.now()}.jpg`);
  if (file) {
    capturedFiles.value.push(file);
    capturedPreviews.value.push(dataUrl);
  }
  
  // 확인 창 띄우기
  isConfirming.value = true;
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
    
    const img = new Image();
    img.onload = () => {
      uploadedImage.value = img;
      if (imageContainerRef.value) {
        const cw = imageContainerRef.value.clientWidth;
        const ch = imageContainerRef.value.clientHeight;
        cropStart.value = { x: cw * 0.1, y: ch * 0.2 };
        cropEnd.value = { x: cw * 0.9, y: ch * 0.8 };
      }
    };
    img.src = previewUrl.value as string;
  };
  reader.readAsDataURL(file);
};

const startCropDrag = (e: MouseEvent | TouchEvent) => {
  const evt = e instanceof MouseEvent ? e : e.touches[0];
  if (!imageContainerRef.value) return;
  const rect = imageContainerRef.value.getBoundingClientRect();
  cropStart.value = { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
  cropEnd.value = { x: evt.clientX - rect.left, y: evt.clientY - rect.top };
  isDraggingCrop.value = true;
};

const moveCropDrag = (e: MouseEvent | TouchEvent) => {
  if (!isDraggingCrop.value || !imageContainerRef.value) return;
  const evt = e instanceof MouseEvent ? e : e.touches[0];
  const rect = imageContainerRef.value.getBoundingClientRect();
  cropEnd.value = { 
    x: Math.max(0, Math.min(rect.width, evt.clientX - rect.left)), 
    y: Math.max(0, Math.min(rect.height, evt.clientY - rect.top)) 
  };
};

const endCropDrag = () => {
  isDraggingCrop.value = false;
};

const applyCropAndUpload = async () => {
  if (!uploadedImage.value || !canvasRef.value || !imageContainerRef.value) return;
  
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
  const croppedDataUrl = canvas.toDataURL('image/jpeg', 0.9);
  
  if (!croppedDataUrl.includes(',')) {
    alert('이미지 크롭에 실패했습니다.');
    return;
  }
  
  // File 객체로 변환하여 배열에 누적
  const file = dataURLtoFile(croppedDataUrl, `crop_${Date.now()}.jpg`);
  if (file) {
    capturedFiles.value.push(file);
    capturedPreviews.value.push(croppedDataUrl);
  }
  
  isCropping.value = false;
  previewUrl.value = null;
  // 확인 창 띄우기
  isConfirming.value = true;
};


// 🚨 추가됨: 이어서 촬영하기, 특정 사진 삭제하기, 최종 전체 업로드하기 함수
const takeAnother = () => {
  isConfirming.value = false;
  previewUrl.value = null;
  startCamera();
};

const removeCaptured = (index: number) => {
  capturedFiles.value.splice(index, 1);
  capturedPreviews.value.splice(index, 1);
  // 만약 다 지웠다면 다시 카메라 화면으로 복귀
  if (capturedFiles.value.length === 0) {
    takeAnother();
  }
};

const uploadAll = async () => {
  if (capturedFiles.value.length === 0) return;
  
  isUploading.value = true;
  try {
    // 누적된 전체 파일 배열을 서버로 전송!
    const response = await startSession(selectedLocation.value || 'UNKNOWN', capturedFiles.value);
    
    // 업로드 성공 시 대기열 비우고 DetailView로 이동
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
    // 🚨 수정됨: Data URL 형식을 갖춘 더미 문자열로 변경
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
  // 화면 UI 및 이벤트 초기 설정
  document.body.classList.add('camera-mode');
  enterFullScreen();
  
  const mq = window.matchMedia("(orientation: portrait)");
  mq.addEventListener("change", handleOrientationChange);

  try {
    // 1. 위치 데이터 로드
    locations.value = await getLocations();
    
    // 2. 지도 뷰에서 넘어온 locationId 파라미터 확인
    const queryLocationId = route.query.locationId;
    
    if (queryLocationId) {
      // 불러온 목록 중에 해당 ID가 있는지 확인
      const matchedLoc = locations.value.find((loc: any) => loc.location_id === queryLocationId);
      
      if (matchedLoc) {
        // 위치 자동 선택
        selectedLocation.value = matchedLoc.location_id; 
        
        // 💡 3. 위치 선택 모달을 숨겨서 바로 카메라 화면으로 진입!
        showLocationModal.value = false; 
      }
    }
  } catch (err) {
    console.error("Failed to load locations", err);
  }
});

onBeforeUnmount(() => {
  // 카메라 떠날 때 camera-mode 제거 → 원래 레이아웃 복원
  document.body.classList.remove('camera-mode');
  exitFullScreen();
  stopCamera();
  const mq = window.matchMedia("(orientation: portrait)");
  mq.removeEventListener("change", handleOrientationChange);
});
</script>

<template>
  <main class="flex-col h-full bg-black relative z-30 flex animate-fade-in">
    <!-- 가로 모드 유도 오버레이 -->
    <div v-if="isPortrait && !isCropping && !showLocationModal" class="absolute inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-6 text-center backdrop-blur-md">
      <div class="text-6xl mb-6 animate-pulse">📱🔄</div>
      <h2 class="text-white text-2xl font-bold mb-4">가로 모드로 전환해주세요</h2>
      <p class="text-stone-300 text-sm">정확한 서가 인식을 위해<br>기기를 가로로 눕혀서 촬영해야 합니다.</p>
    </div>

    <!-- 구역 선택 모달 -->
    <div v-if="showLocationModal" class="absolute inset-0 z-[60] bg-stone-900 flex flex-col p-6 animate-fade-in">
      <div class="flex justify-between items-center mb-6">
        <button @click="router.push('/')" class="text-white text-2xl">◀</button>
        <h2 class="text-white text-xl font-bold">스캔 구역 선택</h2>
        <div class="w-6"></div>
      </div>
      <p class="text-stone-400 text-sm mb-4">점검을 진행할 구역을 선택해주세요.</p>
      <div class="flex-1 overflow-y-auto flex flex-col gap-3">
        <button 
          v-for="loc in locations" 
          :key="loc.location_id"
          @click="selectLocation(loc.location_id)"
          class="bg-stone-800 border border-stone-700 p-4 rounded-xl text-left active:bg-stone-700 transition-colors"
        >
          <div class="text-white font-bold">{{ loc.room_name }} - {{ loc.section }}열</div>
          <div class="text-stone-400 text-xs mt-1">{{ loc.shelf_num }}번 서가 {{ loc.level_num }}단 (ID: {{ loc.location_id }})</div>
        </button>
        <div v-if="locations.length === 0" class="text-stone-500 text-center py-10">
          구역 정보를 불러오는 중이거나 등록된 구역이 없습니다.
        </div>
      </div>
    </div>

    <div class="absolute top-0 w-full z-20 p-4 flex justify-between items-center bg-gradient-to-b from-black/60 to-transparent pb-10 text-white">
      <button @click="router.push('/')" class="text-2xl px-2">◀</button>
      <div class="text-center" v-if="selectedLocation">
        <h1 class="text-sm font-bold">{{ selectedLocation }}</h1>
        <p v-if="!isCropping" class="text-[10px] text-white/70">가이드라인에 맞춰 서가를 촬영해주세요</p>
        <p v-else class="text-[10px] text-white/70">드래그하여 서가 영역을 선택하세요</p>
      </div>
      <button class="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center text-xl active:bg-white/40">⚡</button>
    </div>

    <div 
      ref="imageContainerRef"
      class="flex-1 relative overflow-hidden flex items-center justify-center bg-stone-800"
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
      <img v-if="previewUrl" :src="previewUrl" class="absolute w-full h-full object-contain pointer-events-none z-10" />
      
      <!-- 촬영용 직사각형 가이드 -->
      <div v-if="!previewUrl && !isCameraError" class="absolute border-2 border-white/50 flex flex-col justify-evenly items-center pointer-events-none z-10" style="left: 5%; right: 5%; top: 20%; bottom: 20%; box-shadow: 0 0 0 9999px rgba(0,0,0,0.6);">
        <div class="w-full h-px bg-white/30 absolute top-1/3"></div>
        <div class="w-full h-px bg-white/30 absolute top-2/3"></div>
        <div class="absolute w-px h-full bg-white/30"></div>
        <div class="w-6 h-6 border-l-4 border-t-4 border-[#4CAF50] absolute top-[-2px] left-[-2px]"></div>
        <div class="w-6 h-6 border-r-4 border-t-4 border-[#4CAF50] absolute top-[-2px] right-[-2px]"></div>
        <div class="w-6 h-6 border-l-4 border-b-4 border-[#4CAF50] absolute bottom-[-2px] left-[-2px]"></div>
        <div class="w-6 h-6 border-r-4 border-b-4 border-[#4CAF50] absolute bottom-[-2px] right-[-2px]"></div>
      </div>

      <!-- 크롭용 드래그 박스 -->
      <div v-if="isCropping && cropRect.w > 0" class="absolute z-20 pointer-events-none border-2 border-[#4CAF50] bg-[#4CAF50]/10"
           :style="{ left: cropRect.x + 'px', top: cropRect.y + 'px', width: cropRect.w + 'px', height: cropRect.h + 'px' }">
        <div class="w-3 h-3 bg-white border border-[#4CAF50] absolute -top-1.5 -left-1.5"></div>
        <div class="w-3 h-3 bg-white border border-[#4CAF50] absolute -top-1.5 -right-1.5"></div>
        <div class="w-3 h-3 bg-white border border-[#4CAF50] absolute -bottom-1.5 -left-1.5"></div>
        <div class="w-3 h-3 bg-white border border-[#4CAF50] absolute -bottom-1.5 -right-1.5"></div>
      </div>

      <div v-if="isCameraError && !isCropping" class="absolute inset-0 bg-stone-900 z-20 flex flex-col items-center justify-center p-6 text-center">
        <span class="text-4xl mb-4">🚫</span>
        <h3 class="text-white font-bold mb-2">카메라 권한 필요</h3>
        <p class="text-stone-400 text-xs mb-6">데스크톱 등 카메라가 없는 경우<br>테스트 이미지를 업로드하거나 가상 캡처를 사용하세요.</p>
        <button @click="simulateCapture" class="px-6 py-3 bg-stone-700 text-white rounded-xl font-bold active:bg-stone-600">가상 이미지 캡처</button>
      </div>
    </div>

    <!-- 숨겨진 파일 인풋 -->
    <input type="file" ref="fileInputRef" accept="image/*" class="hidden" @change="handleFileUpload" />

    <div class="h-32 bg-black flex items-center justify-around px-6 shrink-0 relative z-20">
      <button @click="triggerFileUpload" class="w-12 h-12 text-white/80 text-2xl flex items-center justify-center bg-stone-800 rounded-full active:bg-stone-700">
        🖼
      </button>
      
      <button v-if="!isCropping" @click="takePhoto" :disabled="isUploading || isCameraError" class="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center bg-white/20 active:scale-95 transition-all disabled:opacity-50">
        <div class="w-12 h-12 rounded-full bg-white"></div>
      </button>

      <button v-else @click="applyCropAndUpload" :disabled="isUploading" class="px-6 py-3 bg-[#4CAF50] text-white font-bold rounded-full active:scale-95 transition-all disabled:opacity-50 shadow-lg shadow-[#4CAF50]/20">
        크롭 및 업로드
      </button>

      <button v-if="isCropping" @click="() => { isCropping = false; previewUrl = null; startCamera(); }" class="w-12 h-12 text-white/80 text-lg flex items-center justify-center bg-stone-800 rounded-full active:bg-stone-700">
        ✕
      </button>
      <button v-else class="w-12 h-12 text-white/80 text-2xl flex items-center justify-center">
        🔄
      </button>
    </div>
    
    <div v-if="isConfirming" class="absolute inset-0 bg-stone-900 z-[60] flex flex-col items-center justify-center p-6">
      <h2 class="text-white text-2xl font-bold mb-2">서가 촬영 확인</h2>
      <p class="text-stone-400 mb-6 text-sm">왼쪽부터 순서대로 나열되어 있는지 확인해주세요.</p>

      <div class="flex gap-4 overflow-x-auto w-full pb-4 mb-8 snap-x scrollbar-hide">
        <div v-for="(url, idx) in capturedPreviews" :key="idx" class="relative min-w-[140px] h-[200px] snap-center shrink-0">
          <img :src="url" class="w-full h-full object-cover rounded-xl border-2 border-stone-600" />
          <div class="absolute top-0 left-0 bg-black/80 text-white text-xs font-bold px-3 py-1.5 rounded-br-xl rounded-tl-xl">
            {{ idx + 1 }}
          </div>
          <button @click="removeCaptured(idx)" class="absolute top-2 right-2 bg-red-500/90 hover:bg-red-500 rounded-full w-8 h-8 text-white font-bold flex items-center justify-center shadow-md active:scale-90 transition-transform">
            ✕
          </button>
        </div>
      </div>

      <div class="flex flex-col gap-4 w-full max-w-sm mt-auto pb-10">
        <button @click="takeAnother" class="w-full py-4 bg-stone-800 text-white border border-stone-600 rounded-2xl font-bold text-lg active:bg-stone-700 transition-colors">
          ➕ 다음 칸 이어서 촬영
        </button>
        
        <button @click="uploadAll" :disabled="isUploading" class="w-full py-5 bg-[#4CAF50] text-white rounded-2xl font-black text-xl active:scale-95 transition-all shadow-[0_0_20px_rgba(76,175,80,0.3)] disabled:opacity-50">
          <span v-if="!isUploading">🚀 총 {{ capturedFiles.length }}장 분석 시작</span>
          <span v-else>⏳ 업로드 중...</span>
        </button>
      </div>
    </div>

    <!-- 로딩 오버레이 -->
    <div v-if="isUploading" class="absolute inset-0 bg-stone-900/90 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
      <div class="w-16 h-16 border-4 border-stone-600 border-t-green-500 rounded-full animate-spin mb-6"></div>
      <h2 class="text-white font-extrabold text-lg tracking-wide animate-pulse">Vision AI 분석 중...</h2>
      <p class="text-stone-400 text-xs mt-2">청구기호 해독 및 배가 상태 비교</p>
    </div>
  </main>
</template>

