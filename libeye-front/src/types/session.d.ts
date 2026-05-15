// libeye-front/src/types/session.d.ts

// 🚨 새로 추가된 다중 이미지 스키마
export interface ScanImage {
  image_id: string;
  image_url: string;
  sequence_order: number;
}

export interface DetectionResult {
  detection_id: string;
  source_image_id: string | null; // 🚨 추가됨 (어떤 이미지에서 왔는지)
  detected_order: number;         // 🚨 추가됨 (왼쪽부터 최종 병합된 순서)
  bounding_box: { x: number, y: number, w: number, h: number };
  ocr_title: string;              // 🚨 ocr_text -> 분리됨
  ocr_call_number: string;
  status: 'MATCH' | 'MISPLACED' | 'MISSING' | 'EXTRA' | 'UNKNOWN';
  matched_book_id: string | null;
  crop_image_url: string | null;
  confidence: number;
}

export interface SessionResponse {
  session_id: string;
  status: string;
  message?: string;
  images?: ScanImage[]; // 🚨 image_url (단일 string) 대신 객체 배열로 변경됨
  detections?: DetectionResult[];
}
