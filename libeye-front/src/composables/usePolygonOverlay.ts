import { ref } from 'vue';

// --- 이미지 해상도 비율 및 오프셋 계산 + YOLO polygon 좌표 변환 (DetailView 캐러셀용) ---
export function usePolygonOverlay() {
  const imageDimensions = ref<Record<string, { scaleX: number, scaleY: number, offsetX: number, offsetY: number }>>({});

  const onImageLoad = (event: Event, imageId: string) => {
    const img = event.target as HTMLImageElement;

    // 1. 화면에 표시된 컨테이너 크기 vs 실제 원본 이미지 크기
    const containerW = img.clientWidth;
    const containerH = img.clientHeight;
    const naturalW = img.naturalWidth;
    const naturalH = img.naturalHeight;

    // 2. object-contain으로 인한 스케일 비율 계산
    const containerRatio = containerW / containerH;
    const imageRatio = naturalW / naturalH;

    let renderedW, renderedH, offsetX = 0, offsetY = 0;

    if (imageRatio > containerRatio) {
      // 이미지가 컨테이너보다 가로로 길 때 (상하 여백 발생)
      renderedW = containerW;
      renderedH = containerW / imageRatio;
      offsetY = (containerH - renderedH) / 2;
    } else {
      // 이미지가 컨테이너보다 세로로 길 때 (좌우 여백 발생)
      renderedH = containerH;
      renderedW = containerH * imageRatio;
      offsetX = (containerW - renderedW) / 2;
    }

    // 3. 변환된 스케일과 오프셋 저장
    imageDimensions.value[imageId] = {
      scaleX: renderedW / naturalW,
      scaleY: renderedH / naturalH,
      offsetX,
      offsetY
    };
  };

  // --- YOLO polygon 좌표를 SVG points 문자열로 변환 ---
  const getPolygonPoints = (detection: any, imageId: string): string => {
    const dim = imageDimensions.value[imageId];
    if (!dim || !detection.bounding_box) return '';

    // DB에서 JSON 문자열로 넘어올 경우를 대비한 안전한 파싱
    const box = typeof detection.bounding_box === 'string'
      ? JSON.parse(detection.bounding_box)
      : detection.bounding_box;

    if (!box.polygon || box.polygon.length === 0) return '';

    return box.polygon
      .map(([x, y]: [number, number]) =>
        `${dim.offsetX + x * dim.scaleX},${dim.offsetY + y * dim.scaleY}`)
      .join(' ');
  };

  // polygon의 최상단-좌측 꼭짓점 위치를 반환 (배지 위치 계산용)
  const getPolygonLabelPos = (detection: any, imageId: string): { x: number, y: number } | null => {
    const dim = imageDimensions.value[imageId];
    if (!dim || !detection.bounding_box) return null;

    const box = typeof detection.bounding_box === 'string'
      ? JSON.parse(detection.bounding_box)
      : detection.bounding_box;

    if (!box.polygon || box.polygon.length === 0) return null;

    const minX = Math.min(...box.polygon.map(([x]: [number, number]) => x));
    const minY = Math.min(...box.polygon.map(([, y]: [number, number]) => y));

    return {
      x: dim.offsetX + minX * dim.scaleX,
      y: dim.offsetY + minY * dim.scaleY,
    };
  };

  return { imageDimensions, onImageLoad, getPolygonPoints, getPolygonLabelPos };
}
