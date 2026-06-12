import { ref, computed, type Ref } from 'vue';

// 💡 크롭박스 상태 관리 + 드래그/리사이즈 제어 (CameraView 크롭 인터페이스용)
export function useCropBox(imageContainerRef: Ref<HTMLDivElement | null>) {
  // 💡 새로운 크롭박스 상태 관리 (X1, Y1, X2, Y2 절대 좌표 구조)
  const cropBox = ref({ x1: 0, y1: 0, x2: 0, y2: 0 });
  const hasCropBox = ref(false); // 크롭박스가 유효하게 생성되었는지 여부

  // 드래그 액션 상태: 'none' | 'create' | 'move' | 'resize-tl' | 'resize-tr' | 'resize-bl' | 'resize-br'
  const dragAction = ref('none');
  const dragStartOffset = ref({ x: 0, y: 0 }); // 이동/크기조절용 초기 offset
  const initialCropBox = ref({ x1: 0, y1: 0, x2: 0, y2: 0 });

  // 💡 렌더링 및 연산을 위한 computed 크롭박스 (음수 치우침 방지)
  const cropRect = computed(() => {
    const x = Math.min(cropBox.value.x1, cropBox.value.x2);
    const y = Math.min(cropBox.value.y1, cropBox.value.y2);
    const w = Math.abs(cropBox.value.x1 - cropBox.value.x2);
    const h = Math.abs(cropBox.value.y1 - cropBox.value.y2);
    return { x, y, w, h };
  });

  // 💡 헬퍼 함수: 터치/마우스 이벤트에서 컨테이너 기준 좌표 구하기
  const getClientCoords = (e: MouseEvent | TouchEvent) => {
    const evt = e instanceof MouseEvent ? e : e.touches[0];
    if (!imageContainerRef.value) return { x: 0, y: 0 };
    const rect = imageContainerRef.value.getBoundingClientRect();
    return {
      x: evt.clientX - rect.left,
      y: evt.clientY - rect.top
    };
  };

  // 💡 헬퍼 함수: 클릭한 곳이 모서리(핸들)인지 판별 (반경 20px 허용)
  const getResizeHandle = (x: number, y: number) => {
    if (!hasCropBox.value) return 'none';
    const r = 20; // 터치 타겟 영역 반경
    const { x1, y1, x2, y2 } = cropBox.value;

    const left = Math.min(x1, x2);
    const right = Math.max(x1, x2);
    const top = Math.min(y1, y2);
    const bottom = Math.max(y1, y2);

    if (Math.abs(x - left) < r && Math.abs(y - top) < r) return 'resize-tl';
    if (Math.abs(x - right) < r && Math.abs(y - top) < r) return 'resize-tr';
    if (Math.abs(x - left) < r && Math.abs(y - bottom) < r) return 'resize-bl';
    if (Math.abs(x - right) < r && Math.abs(y - bottom) < r) return 'resize-br';

    // 모서리가 아니고 크롭박스 내부인지 확인
    if (x >= left && x <= right && y >= top && y <= bottom) return 'move';

    return 'none';
  };

  // 💡 드래그 시작 통합 제어
  const startCropDrag = (e: MouseEvent | TouchEvent) => {
    if (e.cancelable) e.preventDefault(); // 파란 블록 지정(선택방지) 강제 차단
    const { x, y } = getClientCoords(e);

    const handle = getResizeHandle(x, y);

    if (handle !== 'none') {
      // 1. 모서리 조절 또는 박스 전체 이동
      dragAction.value = handle;
      dragStartOffset.value = { x, y };
      initialCropBox.value = { ...cropBox.value };
    } else {
      // 2. 다른 곳을 터치하면 박스가 사라지지 않고 그 자리에서 새 크롭박스 그리기 시작
      dragAction.value = 'create';
      hasCropBox.value = true;
      cropBox.value = { x1: x, y1: y, x2: x, y2: y };
    }
  };

  // 💡 드래그 중 이동 및 크기 조절 매핑
  const moveCropDrag = (e: MouseEvent | TouchEvent) => {
    if (dragAction.value === 'none' || !imageContainerRef.value) return;
    if (e.cancelable) e.preventDefault();

    const { x, y } = getClientCoords(e);
    const rect = imageContainerRef.value.getBoundingClientRect();

    // 경계 제한 처리용 헬퍼 구하기
    const curX = Math.max(0, Math.min(rect.width, x));
    const curY = Math.max(0, Math.min(rect.height, y));

    const dx = x - dragStartOffset.value.x;
    const dy = y - dragStartOffset.value.y;

    const left = Math.min(initialCropBox.value.x1, initialCropBox.value.x2);
    const right = Math.max(initialCropBox.value.x1, initialCropBox.value.x2);
    const top = Math.min(initialCropBox.value.y1, initialCropBox.value.y2);
    const bottom = Math.max(initialCropBox.value.y1, initialCropBox.value.y2);

    if (dragAction.value === 'create') {
      cropBox.value.x2 = curX;
      cropBox.value.y2 = curY;
    }
    else if (dragAction.value === 'move') {
      // 박스 전체 이동 제한 처리 (화면 밖 방지)
      let moveX = dx;
      let moveY = dy;
      if (left + moveX < 0) moveX = -left;
      if (right + moveX > rect.width) moveX = rect.width - right;
      if (top + moveY < 0) moveY = -top;
      if (bottom + moveY > rect.height) moveY = rect.height - bottom;

      cropBox.value = {
        x1: initialCropBox.value.x1 + moveX,
        y1: initialCropBox.value.y1 + moveY,
        x2: initialCropBox.value.x2 + moveX,
        y2: initialCropBox.value.y2 + moveY
      };
    }
    else {
      // 정규화된 상자 기준 모서리 작동
      if (dragAction.value === 'resize-tl') {
        cropBox.value.x1 = Math.min(right - 10, curX);
        cropBox.value.y1 = Math.min(bottom - 10, curY);
        cropBox.value.x2 = right;
        cropBox.value.y2 = bottom;
      } else if (dragAction.value === 'resize-tr') {
        cropBox.value.x1 = left;
        cropBox.value.y1 = Math.min(bottom - 10, curY);
        cropBox.value.x2 = Math.max(left + 10, curX);
        cropBox.value.y2 = bottom;
      } else if (dragAction.value === 'resize-bl') {
        cropBox.value.x1 = Math.min(right - 10, curX);
        cropBox.value.y1 = top;
        cropBox.value.x2 = right;
        cropBox.value.y2 = Math.max(top + 10, curY);
      } else if (dragAction.value === 'resize-br') {
        cropBox.value.x1 = left;
        cropBox.value.y1 = top;
        cropBox.value.x2 = Math.max(left + 10, curX);
        cropBox.value.y2 = Math.max(top + 10, curY);
      }
    }
  };

  const endCropDrag = () => {
    if (dragAction.value === 'create') {
      // 박스 크기가 너무 작으면 무효화 방지용 최소 기준
      if (cropRect.value.w < 15 || cropRect.value.h < 15) {
        // 기존 박스 유지 또는 복구 처리 가능
      }
    }
    dragAction.value = 'none';
  };

  return { cropBox, hasCropBox, cropRect, startCropDrag, moveCropDrag, endCropDrag };
}
