import { ref, type Ref } from 'vue';

// 💡 카메라 스트림 초기화/해제 제어 (CameraView용)
export function useCameraStream(
  videoRef: Ref<HTMLVideoElement | null>,
  selectedLocation: Ref<string | null>,
) {
  const currentStream = ref<MediaStream | null>(null);
  const imageCapture = ref<any>(null);
  const isCameraReady = ref(false);
  const isCameraError = ref(false);

  const startCamera = async () => {
    if (!selectedLocation.value) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      currentStream.value = stream;
      if (videoRef.value) {
        videoRef.value.srcObject = stream;
        isCameraReady.value = true;
      }

      // 💡 비디오 트랙으로부터 고해상도 ImageCapture 객체 생성
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack && 'ImageCapture' in window) {
        imageCapture.value = new (window as any).ImageCapture(videoTrack);
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
      imageCapture.value = null;
    }
  };

  return { currentStream, imageCapture, isCameraReady, isCameraError, startCamera, stopCamera }
}
