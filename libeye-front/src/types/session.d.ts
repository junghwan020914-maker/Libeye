export interface BoundingBox { x: number; y: number; w: number; h: number; }
export interface DetectionResult {
  id: string;
  box: BoundingBox;
  call_number: string;
  status: 'MATCH' | 'MISPLACED' | 'UNKNOWN' | 'MISSING';
}
export interface SessionStatusResponse {
  session_id: string;
  overall_status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'ERROR';
  detections: DetectionResult[];
}
