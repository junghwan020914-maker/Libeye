// 💡 1~32행 루프 생성 (시각적으로 정돈되도록 1부터 32까지 생성)
export const SHELF_ROWS = Array.from({ length: 32 }, (_, i) => i + 1);

// 💡 A~G열 목록 선언
export const SECTION_LABELS = ['A열', 'B열', 'C열', 'D열', 'E열', 'F열', 'G열'];

// 💡 5단부터 1단까지 역순 배치 (위 -> 아래 사상 반영)
export const SHELF_LEVELS = [5, 4, 3, 2, 1];

// 그리드 레이아웃용 열 알파벳
export const SECTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

// 💡 층(Floor) 목록
export const FLOORS = ['B2', 'B1', '1F', '2F', '3F'];
