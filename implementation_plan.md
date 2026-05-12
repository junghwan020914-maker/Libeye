# Frontend UI Redesign Implementation Plan (UI_Aggregated_2 기반)

제안해주신 `UI_Aggregated_2.html`의 서비스 구성을 바탕으로 Vue.js 프론트엔드 아키텍처를 전면 개편하는 계획입니다. 단순한 화면 전환을 넘어 실제 데이터(세션 API, 결과 API)와 연동되는 배포 수준의 애플리케이션으로 구축합니다.

## User Review Required

> [!IMPORTANT]
> `UI_Aggregated_2.html`은 여러 화면(로그인, 대시보드, 카메라, 히스토리, 맵 등)을 하나에 담고 있습니다. 이를 효율적으로 관리하기 위해 `vue-router`를 세팅하고, 차트 렌더링을 위해 `chart.js` 라이브러리를 추가로 설치하고자 합니다. 아래의 컴포넌트 구조 변경안을 확인하시고 승인해 주시면 즉시 작업을 시작하겠습니다.

## Proposed Changes

### 1. 패키지 설치 및 환경 설정

#### [MODIFY] `package.json`
- `chart.js` 및 `vue-chartjs` 설치 (대시보드 및 통계 차트 구현용)
- `lucide-vue-next` 설치 (아이콘 구현용)

#### [MODIFY] `tailwind.config.js`
- `UI_Aggregated_2.html`의 커스텀 색상(stone 계열, 상태 색상 #2E7D32 등) 및 애니메이션(fade-in, pop-in, slide-up) 추가.

#### [MODIFY] `index.html`
- Pretendard 웹 폰트 적용.

### 2. Vue Router 및 메인 레이아웃 세팅

#### [MODIFY] `src/main.ts` & `src/router/index.ts` (신규)
- `vue-router`를 설정하여 각 View를 라우팅할 수 있도록 구축.
- 라우트: `/login`, `/`, `/camera`, `/history`, `/detail`, `/map`, `/analytics`, `/guide`

#### [MODIFY] `src/App.vue`
- `<router-view>` 및 `UI_Aggregated_2.html`에 있는 하단 GNB(Global Navigation Bar)를 공통 레이아웃으로 배치. (로그인, 카메라 화면 등에서는 GNB 숨김 처리)

### 3. 화면(View) 컴포넌트 분리 구현

#### [NEW] `src/views/LoginView.vue`
- 사번/비밀번호 입력 및 로그인 UI.

#### [NEW] `src/views/DashboardView.vue`
- 진척도 도넛 차트 및 최근 발견 오류 바 차트 연동.
- 카메라 퀵 액션 및 촬영 가이드 이동 버튼.

#### [NEW] `src/views/CameraView.vue` (기존 DirectUploader.vue 대체/확장)
- 카메라 렌즈 화면 및 AR 그리드 가이드라인 구현.
- 플래시, 캡처 등 조작 버튼.
- 기존의 Base64 이미지 캡처 및 AI 서버 전송 로직(`startSession`) 이식.
- 분석 중 로딩 오버레이 구현.

#### [NEW] `src/views/HistoryView.vue`
- 전체 스캔 이력 및 결과 요약 리스트.

#### [NEW] `src/views/DetailView.vue` (기존 ResultStatusList.vue 확장)
- 백엔드에서 반환된 `crop_image_url`, `ocr_title`, `status` 정보를 시각적 AR Box (빨강, 초록, 주황 테두리 등)로 구현.
- 오류 항목 수동 교정 모달 연결.

#### [NEW] `src/views/MapView.vue`
- 서고 도면 및 서가 상태(정상/오류/미점검) 시각화 타일.

#### [NEW] `src/views/AnalyticsView.vue` & `GuideView.vue`
- 주간 인사이트 통계 차트 및 조도 센서 시뮬레이션 가이드 화면.

## Verification Plan

### Automated Tests
- `npm run build`를 통해 빌드 에러가 없는지 확인합니다.

### Manual Verification
- 브라우저 환경에서 모든 탭 간 이동(GNB 네비게이션)이 매끄럽게 되는지 확인합니다.
- Camera 뷰에서 사진을 캡처하면 기존처럼 세션 API를 호출하고 Detail 뷰로 결과를 넘기는 파이프라인이 정상 작동하는지 확인합니다.
