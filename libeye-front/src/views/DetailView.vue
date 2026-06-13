<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAnalysisPolling } from '../composables/useAnalysisPolling';
import {
    searchBooksRaw,
    forceMatchDetection,
    verifyDetection,
    deleteDetection,
    verifyAllDetections
} from '../api/detectionAPI';
import AnalysisLoadingOverlay from '../components/detail/AnalysisLoadingOverlay.vue';
import LocationWarningBanner from '../components/detail/LocationWarningBanner.vue';
import ShelfImageCarousel from '../components/detail/ShelfImageCarousel.vue';
import ShelfInventoryList from '../components/detail/ShelfInventoryList.vue';
import UnexpectedBookList from '../components/detail/UnexpectedBookList.vue';
import BookDetailModal from '../components/detail/BookDetailModal.vue';
import DetailActionBar from '../components/detail/DetailActionBar.vue';
import ManualMatchModal from '../components/detail/ManualMatchModal.vue';
import ImageZoomModal from '../components/detail/ImageZoomModal.vue';

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
        confidence: d.confidence || 0,
        highest_score: d.highest_score ?? 0 // 🌟 최고 매칭 점수 전달
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


const goBack = () => {
    router.push('/history');
};

// 선택된 오배열 도서의 상세 정보를 모달로 띄우기 위한 상태
const selectedMisplaced = ref<any>(null);

// 1. 정상 서가 배치도 (원래 있어야 할 책들을 기준으로 상태 매핑)
const shelfInventory = computed(() => {
    if (!sessionData.value?.expected_books) return [];

    return sessionData.value.expected_books.map((expectedBook: any) => {
        // 현재 도서 ID와 매칭된 탐지 결과들 필터링
        const detections = sessionData.value.detections.filter(
            (d: any) => d.matched_book_id === expectedBook.book_id
        );

        // 🌟 여러 개가 매칭되었다면 중복 오류 상태(DUPLICATE)로 인지
        const isDuplicated = detections.length > 1;

        return {
            ...expectedBook,
            detection: detections[0] || null,
            status: isDuplicated ? 'DUPLICATE' : (detections.length > 0 ? detections[0].status : 'MISSING')
        };
    });
});

// 2. 외부 유입 도서 및 미인식 도서
//    - MISPLACED + 이 서가 소속 아님: assigned_loc_id가 다른 서가 → 타 구역에서 잘못 꽂힌 책
//    - UNKNOWN: 청구기호 인식 실패로 소속 자체를 알 수 없는 책
//    ※ MISPLACED여도 이 서가 expected_books에 있으면 shelfInventory에서 처리됨
const unexpectedDetections = computed(() => {
    if (!sessionData.value?.detections) return [];

    const expectedBookIds = new Set(
        (sessionData.value.expected_books ?? []).map((b: any) => b.book_id)
    );

    return sessionData.value.detections.filter((d: any) =>
        d.status === 'UNKNOWN' ||
        d.status === 'DUPLICATE' || // 🌟 중복 매칭 오류 도서도 수동 교정 대상 리스트에 포함
        (d.status === 'MISPLACED' && !expectedBookIds.has(d.matched_book_id))
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
        highest_score: targetDetection?.highest_score ?? 0, // 🌟 최고 매칭 점수 전달
        // 수동 교정으로 즉시 전하기 위한 원본 디텍션 객체 참조 저장
        _raw_detection: targetDetection
    };
};


const searchQuery = ref('');
const searchResults = ref<any[]>([]);
const isSearching = ref(false);
let searchTimeout: any = null;
const selectedMatchCandidate = ref<any>(null);

// 디바운스(Debounce)를 이용한 실시간 검색 로직
const onSearchInput = () => {
    selectedMatchCandidate.value = null;
    if (!searchQuery.value.trim()) {
        searchResults.value = [];
        return;
    }
    if (searchTimeout) clearTimeout(searchTimeout);
    isSearching.value = true;

    searchTimeout = setTimeout(async () => {
        try {
            const data = await searchBooksRaw(searchQuery.value);
            searchResults.value = data.results || [];
        } catch (e) {
            console.error('검색 오류:', e);
        } finally {
            isSearching.value = false;
        }
    }, 400);
};

// 장서 DB 강제 매칭 처리
const forceMatch = async () => {
    if (!selectedMatchCandidate.value || !editingBook.value) {
        alert('매칭할 도서를 검색하고 선택해주세요.');
        return;
    }
    try {
        await forceMatchDetection(sessionId.value, editingBook.value.detection_id, selectedMatchCandidate.value.book_id);
        closeEditModal();
        window.location.reload(); // API 결과가 재계산되었으므로 새로고침하여 동기화
    } catch (e) {
        alert('강제 매칭 중 오류가 발생했습니다.');
    }
};

// 조치(물리적 이동) 완료 확인 로직
const verifyMisplacement = async () => {
    if (!selectedBook.value) return;
    const rawData = selectedBook.value._raw_detection;

    try {
        await verifyDetection(sessionId.value, rawData.detection_id);
        selectedBook.value = null;
        window.location.reload();
    } catch (e) {
        alert('조치 완료 반영 중 오류가 발생했습니다.');
    }
};

// 모달 종료 시 검색 상태 초기화 업데이트
const closeEditModal = () => {
    showEditModal.value = false;
    editingBook.value = null;
    searchQuery.value = '';
    searchResults.value = [];
    selectedMatchCandidate.value = null;
    showZoomModal.value = false;
};

// 검색 결과 클릭 시
const selectCandidate = (book: any) => {
    selectedMatchCandidate.value = book;
    searchQuery.value = book.call_number;

    // 🚨 [추가됨] 선택을 완료하면 목록을 닫기 위해 배열을 비웁니다.
    searchResults.value = [];
};

// 책이 아닌 객체(False Positive) 무시 및 삭제 로직 (상세창 및 수동교정창 공용)
const ignoreDetection = async () => {
    // 상세창이 열려있으면 selectedBook에서, 수동교정창이면 editingBook에서 ID 추출
    const detectionId = selectedBook.value?._raw_detection?.detection_id || editingBook.value?.detection_id;

    if (!detectionId) return;

    if (!confirm('이 항목을 책이 아닌 것으로 간주하고 목록에서 완전히 삭제하시겠습니까?')) return;

    try {
        await deleteDetection(sessionId.value, detectionId);

        // 어떤 모달이 열려있었든 모두 닫기 및 초기화
        selectedBook.value = null;
        closeEditModal();

        window.location.reload(); // 성공 시 화면 동기화
    } catch (e) {
        alert('탐지 결과 삭제 중 오류가 발생했습니다.');
    }
};

// 일괄 조치 완료 처리 로직
// --- [신규 추가] 일괄 조치 완료 처리 로직 ---
const verifyAllActions = async () => {
    if (!sessionData.value) return;

    // 1. 조치 완료되지 않은 탐지 항목 카운트 (오배열 미조치, 외부도서, 미인식)
    const unverifiedDetections = sessionData.value.detections.filter(
        (d: any) => (d.status === 'MISPLACED' && !d.is_verified) ||
            d.status === 'UNKNOWN'
    );

    // 2. 유실/미인식 도서 카운트 (MISSING)
    const missingBooks = sessionData.value.expected_books?.filter(
        (expected: any) => !sessionData.value.detections.some(
            (d: any) => d.matched_book_id === expected.book_id
        )
    ) || [];

    const totalUnresolved = unverifiedDetections.length + missingBooks.length;

    // 미조치 건수가 1건 이상일 경우 경고 팝업
    if (totalUnresolved > 0) {
        const confirmResult = confirm(`아직 조치/확인되지 않은 사항이 총 ${totalUnresolved}건(오배열, 인식오류, 유실 등) 있습니다.\n정말 일괄(강제) 완료 처리하시겠습니까?`);
        if (!confirmResult) return;
    }

    try {
        await verifyAllDetections(sessionId.value);
        alert('모든 조치가 완료 처리되었습니다.');
        // 완료 후 목록(히스토리) 화면으로 이동
        router.push('/history');
    } catch (e) {
        alert('일괄 조치 완료 처리 중 오류가 발생했습니다.');
        console.error(e);
    }
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
        <AnalysisLoadingOverlay
            v-if="(sessionData?.status?.toUpperCase() !== 'COMPLETED' && sessionData?.status?.toUpperCase() !== 'SUCCESS') && !isError" />

        <!-- Error State -->
        <div v-else-if="isError" class="flex-1 flex flex-col items-center justify-center p-6">
            <p class="text-red-500 font-bold text-lg">서버 연결 오류</p>
            <button @click="router.push('/camera')"
                class="mt-4 px-6 py-3 bg-stone-200 rounded-xl text-stone-700 font-bold">다시 시도하기</button>
        </div>

        <!-- Results State -->
        <template v-else-if="sessionData">

            <!-- 서가 불일치 경고 배너 -->
            <LocationWarningBanner v-if="sessionData.location_warning" :warning="sessionData.location_warning" />

            <!-- 이미지 캐러셀 + polygon 오버레이 -->
            <ShelfImageCarousel :images="sessionData.images" :detections="sessionData.detections" />

            <div class="flex-1 overflow-y-auto p-4 pb-20 flex flex-col gap-6 bg-stone-100">

                <ShelfInventoryList :items="shelfInventory" @select="openBookDetail" />

                <UnexpectedBookList v-if="unexpectedDetections.length > 0" :detections="unexpectedDetections"
                    @select="openBookDetail" @edit="openEditModal" />
            </div>

            <!-- 도서 상세 정보 모달 -->
            <BookDetailModal v-if="selectedBook" :book="selectedBook" @close="selectedBook = null"
                @verify="verifyMisplacement" @edit="switchFromDetailToEdit" @ignore="ignoreDetection"
                @zoom="openZoom" />

            <DetailActionBar @go-list="router.push('/history')" @verify-all="verifyAllActions" />

            <!-- Edit Modal -->
            <ManualMatchModal v-if="showEditModal" :editing-book="editingBook" :search-query="searchQuery"
                :search-results="searchResults" :is-searching="isSearching"
                :selected-candidate="selectedMatchCandidate" @update:search-query="searchQuery = $event"
                @search-input="onSearchInput" @select-candidate="selectCandidate" @close="closeEditModal"
                @match="forceMatch" @ignore="ignoreDetection" @zoom="openZoom" />

            <!-- 이미지 확대 모달 -->
            <ImageZoomModal v-if="showZoomModal" :image="zoomedImage" @close="closeZoom" />
        </template>
    </main>
</template>
