# 죽은 코드(Dead Code) 목록

> 2026-06 프로젝트 구조 리팩토링 시 **의도적으로 삭제하지 않고 유지**한 미사용 코드 목록입니다.
> 리팩토링의 원칙이 "기능·동작 100% 불변"이었기 때문에, 어디서도 사용되지 않는 코드도 그대로 두고 이 문서에 기록만 합니다.
> 아래 항목들은 향후 별도 정리 PR에서 안전하게 삭제할 수 있는 후보입니다.

## 1. 미사용 컴포넌트

| 파일 | 설명 |
|---|---|
| `src/components/HelloWorld.vue` | Vite 초기 스캐폴드 잔재. 어디서도 import되지 않음. `vite.svg`, `vue.svg`, `hero.png`의 유일한 사용처. |
| `src/components/uploader/DirectUploader.vue` | 파일 직접 업로드 방식의 레거시 플로우. CameraView(촬영+크롭)로 대체됨. 라우터/뷰 어디에도 연결되지 않음. `LOC-A-1-3` 위치가 하드코딩되어 있음. |
| `src/components/dashboard/ResultStatusList.vue` | 죽은 코드인 `DirectUploader.vue`에서만 import됨. DirectUploader 삭제 시 함께 삭제 가능. |

## 2. 미사용 import / 상태 / 함수 (파일 내 잔존)

| 위치 | 항목 | 설명 |
|---|---|---|
| `src/views/DashboardView.vue` | `import CartServiceCard` | import만 되어 있고 템플릿에서 렌더링되지 않음 |
| `src/views/DashboardView.vue` | 빈 `onMounted(() => { ... })` | 내용 없는 라이프사이클 훅 |
| `src/views/DetailView.vue` | `selectedMisplaced` ref, `openMisplacedDetail()` | 템플릿 어디에서도 참조되지 않음 |
| `src/views/CameraView.vue` | `selectLocation()` | 어디서도 호출되지 않음 (`LocationSelectModal`의 `handleFinalSelect`가 실제 사용 경로) |

## 3. 미사용 에셋

| 파일 | 설명 |
|---|---|
| `src/assets/vite.svg` | 죽은 `HelloWorld.vue`에서만 참조 |
| `src/assets/vue.svg` | 죽은 `HelloWorld.vue`에서만 참조 |
| `src/assets/hero.png` | 죽은 `HelloWorld.vue`에서만 참조 |
| `src/assets/image_example.png` | 어디서도 참조되지 않음 (993KB) |

※ `src/assets/logo.png`는 DashboardView 헤더에서 **사용 중**입니다. 삭제 금지.

## 4. no-op CSS 클래스 (정의가 없거나 닿지 않음)

| 위치 | 클래스 | 설명 |
|---|---|---|
| DetailView의 이미지 줌 모달 | `animate-scale-up` | 어디에도 정의가 없음 (tailwind.config.js에는 `scale-up` 미정의). 현재 애니메이션 없이 표시됨. 정의를 추가하면 시각적 동작이 바뀌므로 그대로 유지. |
| DetailView의 이미지 캐러셀 | `scrollbar-hide` | 정의가 CameraView의 scoped 스타일에만 있어 DetailView에는 적용되지 않음 (스크롤바 보임) |
| HistoryView의 필터 탭 | `no-scrollbar` | DashboardView scoped 스타일에만 정의되어 있어 HistoryView에는 적용되지 않음 |

## 5. 알려진 기존 이슈 (이번 리팩토링에서 수정하지 않음)

리팩토링 전 `npm run build`(`vue-tsc -b`)는 아래 **기존 에러 8개**로 이미 실패하는 상태였습니다 (번들링 `npx vite build`는 성공). 기능 불변 원칙에 따라 수정하지 않았습니다.

1. `src/composables/useAnalysisPolling.ts(4)` — `types/session`에 없는 `SessionStatusResponse`를 import (실제 export는 `SessionResponse`)
2. `src/components/dashboard/ResultStatusList.vue(12)` — `unknownBooks` 선언 후 미사용 (TS6133)
3. `src/views/AnalyticsView.vue(30, 39)` — Chart.js doughnut dataset에 `cutout` 속성 타입 에러 (TS2353) × 2
4. `src/views/CameraView.vue` — `selectLocation` 미사용 (TS6133)
5. `src/views/CartResultView.vue(24)` — `'string | number' + number` 연산자 타입 에러 (TS2365)
6. `src/views/DashboardView.vue` — `CartServiceCard` import 미사용 (TS6133)
7. `src/views/DetailView.vue` — `openMisplacedDetail` 미사용 (TS6133)

기타:
- `src/views/MapView.vue`의 `currentGrid`는 3F 외의 층에서 항상 빈 배열을 반환 (다른 층 그리드는 미구현 placeholder)
