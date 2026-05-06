export interface Detection {
  type: string;
  bbox: [number, number, number, number];
}

export interface FileData {
  id: string;
  name: string;
  url: string;
  detections: Detection[];
  redactions: any[];
}