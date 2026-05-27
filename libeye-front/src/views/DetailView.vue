<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisPolling } from '../composables/useAnalysisPolling';

const route = useRoute();
const router = useRouter();

const sessionId = computed(() => route.query.sessionId as string | null);
const { data: sessionData, isError } = useAnalysisPolling(sessionId);

const showEditModal = ref(false);
const showZoomModal = ref(false);
// [추가] 현재 수동 교정 중인 도서의 상세 AI 인식 결과 상태 변수
const editingBook = ref<any>(null);

// 🌟 [신규 추가] 확대 보기 전용 상태 객체
const zoomedImage = ref<any>(null);

// 🌟 [신규 추가] 어느 모달에서든 순수하게 이미지만 확대하는 함수
const openZoom = (bookData: any) => {
    zoomedImage.value = bookData;
    showZoomModal.value = true;
};

// 🌟 [신규 추가] 확대창 닫기 및 초기화 함수
const closeZoom = () => {
    showZoomModal.value = false;
    zoomedImage.value = null;
};

// [추가] 수동 교정 팝업을 열 때 도서 데이터를 매핑해주는 함수
// [업데이트] 수동 교정 모달 진입 함수
const openEditModal = (d: any) => {
    editingBook.value = {
        detection_id: d.detection_id,
        crop_image_url: d.crop_image_url || null,
        ocr_title: d.ocr_title || d.raw_ocr_title || '인식된 제목 없음',
        ocr_call_number: d.ocr_call_number || d.raw_ocr_call_number || '',
        confidence: d.confidence || 0
    };
    showEditModal.value = true;
};

// [추가] 상세 정보창에서 "오류 수정하기" 버튼을 눌렀을 때 교정 폼으로 Context를 전환하는 함수
const switchFromDetailToEdit = () => {
    if (!selectedBook.value) return;
    const rawData = selectedBook.value._raw_detection;

    // 1. 기존 상세창은 닫음
    selectedBook.value = null;
    // 2. 수동 교정 모달 데이터 세팅 후 오픈
    openEditModal(rawData);
};

// [추가] 모달을 닫을 때 상태를 초기화하는 함수
const closeEditModal = () => {
    showEditModal.value = false;
    editingBook.value = null;
    showZoomModal.value = false;
};

const goBack = () => {
    router.push('/history');
};

// --- [추가된 핵심 로직] 이미지 해상도 비율 및 오프셋 계산 ---
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

// --- [추가된 핵심 로직] YOLO polygon 좌표를 SVG points 문자열로 변환 ---
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


// 선택된 오배열 도서의 상세 정보를 모달로 띄우기 위한 상태
const selectedMisplaced = ref<any>(null);

// 1. 정상 서가 배치도 (원래 있어야 할 책들을 기준으로 상태 매핑)
const shelfInventory = computed(() => {
    if (!sessionData.value?.expected_books) return [];

    return sessionData.value.expected_books.map((expectedBook: any) => {
        // 탐지된 결과 중 이 책과 매칭된 데이터가 있는지 확인
        const detection = sessionData.value.detections.find(
            (d: any) => d.matched_book_id === expectedBook.book_id
        );

        return {
            ...expectedBook,
            detection: detection || null,
            // 매칭된 결과가 없으면 MISSING (유실됨)
            status: detection ? detection.status : 'MISSING'
        };
    });
});

// 2. 외계 도서 (이 서가 소속이 아닌데 발견된 책 - EXTRA, UNKNOWN)
const unexpectedDetections = computed(() => {
    if (!sessionData.value?.detections) return [];

    return sessionData.value.detections.filter((d: any) =>
        d.status === 'EXTRA' || d.status === 'UNKNOWN' || (!d.matched_book_id && d.status !== 'MISSING')
    );
});

const openMisplacedDetail = (item: any) => {
    if (item.status === 'MISPLACED') {
        selectedMisplaced.value = item;
    }
};

// 선택된 도서의 상세 팝업 정보를 저장하기 위한 통합 상태 변수
const selectedBook = ref<any>(null);

// 리스트의 어떤 도서(정상, 오배열, 외부 유입 등)를 누르더라도 호출 가능한 팝업 활성화 함수
// [업데이트] 통합 도서 팝업 활성화 함수 (수동 교정 연동을 위해 원본 raw 데이터 주소 보존)
const openBookDetail = (item: any) => {
    // 수동 교정창으로 바로 진입할 때를 위해 원본 매칭/디텍션 객체를 데이터 내부에 유지
    const targetDetection = item.detection || item;

    selectedBook.value = {
        title: item.title || item.ocr_title || '도서명 미상',
        call_number: item.call_number || item.ocr_call_number || '청구기호 판독불가',
        location: item.assigned_loc_id || sessionData.value?.location_id || '알 수 없음',
        expected_order: item.expected_order || '해당 없음',
        detected_order: targetDetection?.detected_order || '미탐지',
        crop_image_url: targetDetection?.crop_image_url || null,
        status: item.status,
        confidence: targetDetection?.confidence || 0,
        // 수동 교정으로 즉시 전하기 위한 원본 디텍션 객체 참조 저장
        _raw_detection: targetDetection
    };
};

</script>

<template>
    <main class="flex-col h-full bg-stone-50 z-30 animate-fade-in absolute inset-0 w-full flex">
        <header class="bg-white px-4 py-3 border-b border-stone-200 flex items-center justify-between shrink-0">
            <button @click="goBack" class="p-2 text-stone-600 text-xl font-bold">◀</button>
            <div class="text-center">
                <h1 class="text-sm font-extrabold text-stone-900">상세 분석 및 조치</h1>

                <p class="text-[9px] text-stone-500">
                    {{ sessionData?.location_name || sessionData?.location_id || '위치 정보 로딩 중...' }}
                </p>
            </div>
            <div class="w-10"></div>
        </header>

        <!-- Polling Loading State -->
        <div v-if="(sessionData?.status?.toUpperCase() !== 'COMPLETED' && sessionData?.status?.toUpperCase() !== 'SUCCESS') && !isError"
            class="flex-1 flex flex-col items-center justify-center p-6 bg-stone-900/90 text-white">
            <div class="w-16 h-16 border-4 border-stone-600 border-t-green-500 rounded-full animate-spin mb-6"></div>
            <h2 class="font-extrabold text-lg tracking-wide animate-pulse">Vision AI 분석 중...</h2>
            <p class="text-stone-400 text-xs mt-2">청구기호 해독 및 배가 상태 비교</p>
        </div>

        <!-- Error State -->
        <div v-else-if="isError" class="flex-1 flex flex-col items-center justify-center p-6">
            <p class="text-red-500 font-bold text-lg">서버 연결 오류</p>
            <button @click="router.push('/camera')"
                class="mt-4 px-6 py-3 bg-stone-200 rounded-xl text-stone-700 font-bold">다시 시도하기</button>
        </div>

        <!-- Results State -->
        <template v-else-if="sessionData">

            <!-- 서가 불일치 경고 배너 -->
            <div v-if="sessionData.location_warning"
                class="bg-amber-50 border-b border-amber-300 px-4 py-2.5 flex items-start gap-2 shrink-0">
                <span class="text-amber-500 text-base leading-none mt-0.5">⚠</span>
                <div class="text-xs text-amber-800 leading-snug">
                    <span class="font-bold">서가 불일치 감지</span><br/>
                    선택한 서가(<span class="font-mono font-semibold">{{ sessionData.location_warning.selected_location_id }}</span>)와
                    실제 스캔된 책들의 서가(<span class="font-mono font-semibold">{{ sessionData.location_warning.actual_location_id }}</span>)가 다릅니다.
                    올바른 서가를 선택하고 다시 스캔해주세요.
                </div>
            </div>

            <div
                class="h-48 bg-stone-300 relative flex overflow-x-auto overflow-y-hidden snap-x shrink-0 shadow-inner scrollbar-hide">

                <div v-if="!sessionData.images || sessionData.images.length === 0"
                    class="absolute inset-0 flex justify-center items-center opacity-30 text-5xl w-full">📚📚📚</div>

                <div v-for="img in sessionData.images" :key="img.image_id"
                    class="relative h-full min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center border-r-2 border-stone-800/40">

                    <img :src="img.image_url" @load="(e) => onImageLoad(e, img.image_id)"
                        class="absolute inset-0 w-full h-full object-contain opacity-50" />

                    <!-- SVG polygon 오버레이 -->
                    <svg class="absolute inset-0 w-full h-full pointer-events-none z-10">
                        <template v-for="d in sessionData.detections" :key="d.detection_id">
                            <polygon
                                v-if="d.source_image_id === img.image_id && d.status !== 'MATCH' && getPolygonPoints(d, img.image_id)"
                                :points="getPolygonPoints(d, img.image_id)"
                                stroke-width="2"
                                :stroke="d.status === 'MATCH' ? '#2E7D32' : d.status === 'MISPLACED' ? '#D32F2F' : '#F57C00'"
                                :fill="d.status === 'MATCH' ? 'rgba(34,197,94,0.1)' : d.status === 'MISPLACED' ? 'rgba(211,47,47,0.3)' : 'rgba(245,124,0,0.3)'"
                            />
                        </template>
                    </svg>

                    <!-- 배지 레이어 (순서 번호 + 상태 텍스트) -->
                    <template v-for="d in sessionData.detections" :key="`badge-${d.detection_id}`">
                        <template v-if="d.source_image_id === img.image_id && d.status !== 'MATCH' && getPolygonLabelPos(d, img.image_id)">
                            <span
                                class="absolute bg-stone-800 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full font-bold shadow-md z-20"
                                :style="{
                                    left: `${getPolygonLabelPos(d, img.image_id)!.x}px`,
                                    top: `${getPolygonLabelPos(d, img.image_id)!.y - 24}px`
                                }">
                                {{ d.detected_order }}
                            </span>
                            <span v-if="d.status !== 'MATCH'"
                                class="absolute bg-white border text-[8px] px-1 rounded whitespace-nowrap z-20"
                                :style="{
                                    left: `${getPolygonLabelPos(d, img.image_id)!.x + 24}px`,
                                    top: `${getPolygonLabelPos(d, img.image_id)!.y - 20}px`
                                }"
                                :class="{
                                    'border-[#D32F2F] text-[#D32F2F]': d.status === 'MISPLACED',
                                    'border-[#F57C00] text-[#F57C00]': d.status === 'UNKNOWN' || d.status === 'MISSING'
                                }">
                                {{ d.status === 'MISPLACED' ? '오배열' : '확인요망' }}
                            </span>
                        </template>
                    </template>
                </div>
            </div>

            <div class="flex-1 overflow-y-auto p-4 pb-20 flex flex-col gap-6 bg-stone-100">

                <section>
                    <h3 class="text-xs font-bold text-stone-500 mb-3 ml-1 flex items-center justify-between">
                        <span>본 서가 등록 도서 목록</span>
                        <span class="bg-stone-300 text-stone-700 px-2 py-0.5 rounded-full text-[9px]">
                            총 {{ shelfInventory.length }}권
                        </span>
                    </h3>
                    <div class="flex flex-col gap-2">
                        <template v-for="item in shelfInventory" :key="item.book_id">

                            <div v-if="item.status === 'MATCH'" @click="openBookDetail(item)"
                                class="bg-white p-3 rounded-lg border border-stone-200 flex items-center justify-between cursor-pointer hover:bg-stone-50 transition-colors shadow-sm">
                                <div class="flex items-center gap-3">
                                    <img v-if="item.detection?.crop_image_url" :src="item.detection.crop_image_url"
                                        class="w-8 h-12 object-cover rounded shadow-sm border border-stone-200 bg-stone-100" />
                                    <div v-else
                                        class="w-8 h-12 bg-stone-100 rounded border border-stone-200 flex items-center justify-center text-[10px] text-stone-400">
                                        정상</div>
                                    <div>
                                        <div class="text-xs font-bold text-stone-800">{{ item.call_number }}</div>
                                        <div class="text-[10px] text-stone-500 mt-0.5 w-48 truncate">{{ item.title }}
                                        </div>
                                    </div>
                                </div>
                                <span
                                    class="text-[10px] font-bold text-green-600 bg-green-50 px-2 py-1 rounded">제자리</span>
                            </div>

                            <div v-else-if="item.status === 'MISPLACED'" @click="openBookDetail(item)"
                                class="bg-red-50 p-3 rounded-lg border-2 border-red-300 flex items-center justify-between cursor-pointer hover:bg-red-100 transition-colors shadow-sm">
                                <div class="flex items-center gap-3">
                                    <img v-if="item.detection?.crop_image_url" :src="item.detection.crop_image_url"
                                        class="w-8 h-12 object-cover rounded shadow-sm border border-red-300" />
                                    <div>
                                        <div class="text-xs font-bold text-red-900 flex items-center gap-1">
                                            <span
                                                class="bg-red-500 text-white text-[9px] px-1.5 py-0.5 rounded shadow-sm">순서오류</span>
                                            {{ item.call_number }}
                                        </div>
                                        <div class="text-[10px] text-red-700 mt-0.5 w-40 truncate">{{ item.title }}
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right flex flex-col items-end gap-1">
                                    <span class="text-[10px] text-stone-400">자세히 보기 ❯</span>
                                </div>
                            </div>

                            <div v-else-if="item.status === 'MISSING'"
                                class="bg-stone-50 p-3 rounded-lg border border-dashed border-stone-400 flex items-center justify-between opacity-80">
                                <div class="flex items-center gap-3">
                                    <div
                                        class="w-8 h-12 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-[12px] font-bold text-stone-500 opacity-60">
                                        ?</div>
                                    <div>
                                        <div class="text-xs font-bold text-stone-600 flex items-center gap-1">
                                            <span class="bg-stone-600 text-white text-[8px] px-1 rounded">유실/미인식</span>
                                            {{ item.call_number }}
                                        </div>
                                        <div class="text-[10px] text-stone-500 mt-0.5 w-48 truncate">{{ item.title }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </section>

                <section v-if="unexpectedDetections.length > 0">
                    <h3 class="text-xs font-bold text-orange-600 mb-3 ml-1 flex items-center gap-1">
                        <span>⚠️ 잘못 꽂힌 타 구역 도서 및 미인식 도서</span>
                    </h3>
                    <div class="flex flex-col gap-2">
                        <template v-for="d in unexpectedDetections" :key="d.detection_id">

                            <div v-if="d.status === 'EXTRA'"
                                class="bg-orange-50 p-3 rounded-lg border border-orange-300 flex items-center justify-between shadow-sm">
                                <div class="flex items-center gap-3" @click="openBookDetail(d)">
                                    <img v-if="d.crop_image_url" :src="d.crop_image_url"
                                        class="w-8 h-12 object-cover rounded shadow-sm border border-orange-400" />
                                    <div>
                                        <div class="text-xs font-bold text-orange-900 flex items-center gap-1">
                                            <span class="bg-orange-500 text-white text-[8px] px-1 rounded">외부도서</span>
                                            {{ d.ocr_call_number || d.ocr_title }}
                                        </div>
                                        <div
                                            class="text-[10px] text-orange-800 mt-1 bg-white inline-block px-2 py-0.5 rounded border border-orange-200">
                                            원래 위치: <strong>{{ d.assigned_loc_id || '알 수 없음' }}</strong>
                                        </div>
                                    </div>
                                </div>
                                <button @click.stop="openEditModal(d)"
                                    class="bg-orange-600 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0 ml-2">수동교정</button>
                            </div>

                            <div v-else-if="d.status === 'UNKNOWN'"
                                class="bg-stone-100 p-3 rounded-lg border border-stone-300 flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <img v-if="d.crop_image_url" :src="d.crop_image_url"
                                        class="w-8 h-12 object-cover rounded shadow-sm border border-stone-300" />
                                    <div>
                                        <div class="text-xs font-bold text-stone-700 flex items-center gap-1">
                                            <span class="bg-stone-500 text-white text-[8px] px-1 rounded">미인식</span> {{
                                                d.ocr_call_number || '해독 불가' }}
                                        </div>
                                        <div class="text-[10px] text-stone-500 mt-0.5">신뢰도 {{ Math.round(d.confidence) }}%</div>
                                    </div>
                                </div>
                                <button @click="openEditModal(d)"
                                    class="bg-stone-800 text-white px-3 py-1.5 rounded text-[10px] font-bold shadow shrink-0">수동교정</button>
                            </div>

                        </template>
                    </div>
                </section>
            </div>


            <div v-if="selectedBook" class="absolute inset-0 bg-stone-900/60 z-50 flex items-center justify-center p-4">
                <div
                    class="bg-white w-full max-w-sm rounded-2xl p-6 flex flex-col animate-slide-up shadow-2xl border border-stone-200">

                    <div class="flex justify-between items-start mb-3 border-b border-stone-100 pb-3">
                        <div>
                            <h2 class="text-base font-extrabold text-stone-900 flex items-center gap-2">
                                <span>도서 상세 정보</span>
                                <span v-if="selectedBook.status === 'MATCH'"
                                    class="text-[10px] font-bold bg-green-100 text-green-700 px-2 py-0.5 rounded-full">정상
                                    배치</span>
                                <span v-else-if="selectedBook.status === 'MISPLACED'"
                                    class="text-[10px] font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">순서
                                    오류</span>
                                <span v-else-if="selectedBook.status === 'EXTRA'"
                                    class="text-[10px] font-bold bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">타
                                    구역
                                    도서</span>
                            </h2>
                        </div>
                        <button @click="selectedBook = null"
                            class="text-stone-400 text-2xl leading-none hover:text-stone-600 transition-colors">✕</button>
                    </div>

                    <div
                        class="flex flex-col items-center bg-stone-50 py-3 rounded-xl mb-4 border border-stone-100 shadow-inner gap-2">
                        <img v-if="selectedBook.crop_image_url" :src="selectedBook.crop_image_url"
                            class="h-40 object-contain rounded shadow border border-stone-200 bg-white" />
                        <div v-else
                            class="h-40 w-24 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-xs text-stone-500">
                            크롭 사진 없음</div>

                        <button v-if="selectedBook.crop_image_url"
                            @click="openZoom(selectedBook._raw_detection || selectedBook)" type="button"
                            class="flex items-center gap-1 bg-white text-stone-700 border border-stone-300 px-2.5 py-1.5 rounded-md text-[10px] font-bold shadow-sm active:bg-stone-50 transition-colors">
                            <span>🔍</span> 이미지 크게 보기
                        </button>
                    </div>

                    <div class="flex flex-col gap-2 bg-stone-50 p-3.5 rounded-xl text-xs text-stone-700 mb-4">
                        <div class="flex flex-col gap-0.5">
                            <span class="text-[10px] font-bold text-stone-400">DB 장서 도서명</span>
                            <span class="font-bold text-stone-900 break-all line-clamp-1">{{ selectedBook.title
                            }}</span>
                        </div>
                        <div class="border-t border-stone-200/60 my-0.5"></div>

                        <div class="grid grid-cols-2 gap-2">
                            <div class="flex flex-col gap-0.5">
                                <span class="text-[10px] font-bold text-stone-400">청구기호</span>
                                <span class="font-semibold text-stone-800 font-mono">{{ selectedBook.call_number
                                }}</span>
                            </div>
                            <div class="flex flex-col gap-0.5">
                                <span class="text-[10px] font-bold text-stone-400">배정 서가 위치</span>
                                <span class="font-semibold text-stone-800">{{ selectedBook.location }}</span>
                            </div>
                        </div>
                        <div class="border-t border-stone-200/60 my-0.5"></div>

                        <div class="grid grid-cols-2 gap-2">
                            <div class="flex flex-col gap-0.5">
                                <span class="text-[10px] font-bold text-stone-400">원래 정위치 순서</span>
                                <span class="font-extrabold text-green-600">{{ selectedBook.expected_order }}번째</span>
                            </div>
                            <div class="flex flex-col gap-0.5">
                                <span class="text-[10px] font-bold text-stone-400">현재 탐지된 순서</span>
                                <span class="font-extrabold"
                                    :class="selectedBook.status === 'MISPLACED' ? 'text-red-500' : 'text-stone-600'">{{
                                        selectedBook.detected_order }}번째</span>
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-col gap-2">
                        <button @click="switchFromDetailToEdit" type="button"
                            class="w-full bg-stone-100 text-stone-600 hover:text-stone-900 border border-stone-300 font-bold py-2 rounded-xl text-[11px] transition-colors flex items-center justify-center gap-1">
                            ✏️ 인식을 잘못했나요? 수동 교정하기
                        </button>

                        <button @click="selectedBook = null"
                            class="w-full bg-stone-800 text-white font-bold py-3 rounded-xl text-xs hover:bg-stone-700 transition-colors shadow-md">
                            확인 완료
                        </button>
                    </div>

                </div>
            </div>

            <div class="absolute bottom-0 w-full bg-white border-t border-stone-200 p-3 flex gap-2">
                <button class="flex-1 bg-stone-100 text-stone-700 text-xs font-bold py-3 rounded-xl">임시 저장</button>
                <button @click="router.push('/history')"
                    class="flex-[2] bg-[#2E7D32] text-white text-xs font-bold py-3 rounded-xl">조치 완료 및 반영</button>
            </div>

            <!-- Edit Modal -->
            <div v-if="showEditModal" class="absolute inset-0 bg-stone-900/60 z-50 flex items-end justify-center"
                @click.self="closeEditModal">
                <div
                    class="bg-white w-full rounded-t-3xl p-6 flex flex-col gap-4 animate-slide-up max-h-[85vh] overflow-y-auto relative">

                    <div class="flex justify-between items-center border-b border-stone-100 pb-2">
                        <div>
                            <h3 class="text-sm font-extrabold text-stone-900">도서 정보 수동 교정</h3>
                            <p class="text-[10px] text-stone-400 mt-0.5">Vision AI가 해독하지 못한 청구기호를 수동으로 입력합니다.</p>
                        </div>
                        <button @click="closeEditModal" class="text-stone-400 text-xl p-1">✕</button>
                    </div>

                    <div
                        class="flex flex-col items-center bg-stone-50 p-3 rounded-xl border border-stone-100 shadow-inner gap-2">
                        <div class="relative group max-w-[120px]">
                            <img v-if="editingBook?.crop_image_url" :src="editingBook.crop_image_url"
                                class="h-36 object-contain rounded shadow border border-stone-200 bg-white" />
                            <div v-else
                                class="h-36 w-20 bg-stone-200 rounded border border-stone-300 flex items-center justify-center text-[10px] text-stone-500">
                                책등 이미지 없음</div>
                        </div>

                        <button v-if="editingBook?.crop_image_url" @click="openZoom(editingBook)" type="button"
                            class="flex items-center gap-1 bg-white text-stone-700 border border-stone-300 px-3 py-1.5 rounded-lg text-[10px] font-bold shadow-sm active:bg-stone-50 transition-colors">
                            <span>🔍</span> 이미지 크게 보기
                        </button>
                    </div>

                    <div class="bg-stone-50 p-2.5 rounded-lg text-[10px] text-stone-600 flex flex-col gap-1 font-mono">
                        <div>🤖 <strong>AI OCR 결과:</strong> {{ editingBook?.ocr_call_number || '판독 불가' }}</div>
                        <div>🎯 <strong>추론 신뢰도:</strong> {{ editingBook ? Math.round(editingBook.confidence) : 0
                            }}%</div>
                    </div>

                    <div class="flex flex-col gap-3">
                        <div class="flex flex-col gap-1">
                            <label class="text-[11px] font-bold text-stone-500">청구기호 입력</label>
                            <input type="text" :placeholder="editingBook?.ocr_call_number || '예: 813.6 김12가'"
                                class="border border-stone-300 rounded-xl p-3 text-xs font-mono focus:outline-none focus:border-stone-800" />
                        </div>

                        <div class="flex flex-col gap-1">
                            <label class="text-[11px] font-bold text-stone-500">도서명 입력 (선택)</label>
                            <input type="text" :placeholder="editingBook?.ocr_title"
                                class="border border-stone-300 rounded-xl p-3 text-xs focus:outline-none focus:border-stone-800" />
                        </div>
                    </div>

                    <div class="flex gap-2 mt-2">
                        <button @click="closeEditModal"
                            class="flex-1 bg-stone-100 text-stone-700 text-xs font-bold py-3.5 rounded-xl">
                            취소
                        </button>
                        <button @click="closeEditModal"
                            class="flex-[2] bg-stone-800 text-white text-xs font-bold py-3.5 rounded-xl shadow-md">
                            장서 DB 강제 매칭
                        </button>
                    </div>

                </div>
            </div>

            <div v-if="showZoomModal"
                class="absolute inset-0 bg-stone-950/95 z-[60] flex flex-col items-center justify-center p-4 animate-fade-in"
                @click="closeZoom">

                <div class="absolute top-6 right-6 flex items-center gap-4 z-10">
                    <span
                        class="text-white/60 text-xs font-medium bg-black/40 px-3 py-1.5 rounded-full backdrop-blur-sm">화면
                        터치
                        시 닫힘</span>
                    <button @click="closeZoom"
                        class="bg-white/10 hover:bg-white/20 text-white w-10 h-10 rounded-full flex items-center justify-center text-xl backdrop-blur-sm transition-colors">✕</button>
                </div>

                <div class="w-full max-w-md max-h-[75vh] flex items-center justify-center overflow-hidden p-2">
                    <img :src="zoomedImage?.crop_image_url"
                        class="max-w-full max-h-[72vh] object-contain rounded-lg shadow-2xl border border-white/10 animate-scale-up"
                        @click.stop />
                </div>

                <div class="mt-4 bg-black/60 backdrop-blur-md text-white border border-white/10 px-5 py-3 rounded-2xl max-w-xs text-center shadow-lg"
                    @click.stop>
                    <div class="text-[10px] text-white/50 font-bold uppercase tracking-wider mb-0.5">AI 인식 텍스트</div>
                    <div class="text-xs font-mono font-bold text-orange-400 truncate">
                        {{ zoomedImage?.ocr_call_number || zoomedImage?.call_number || '판독 불가' }}
                    </div>
                </div>
            </div>
        </template>
    </main>
</template>

