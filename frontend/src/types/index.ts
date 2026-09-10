export interface Location {
  latitude: number;
  longitude: number;
  bbox?: [number, number, number, number];
  name?: string;
}

export interface SatelliteImage {
  image_id: string;
  image_url: string;
  date: string;
  satellite: string;
  bbox: [number, number, number, number];
  metadata: {
    cloud_cover?: number;
    resolution?: number;
    [key: string]: any;
  };
}

export interface AnalysisResponse {
  answer: string;
  confidence: number;
  observations: string[];
  limitations: string[];
  regions?: ChangedRegion[];
}

export interface ChangedRegion {
  id: number;
  bbox: [number, number, number, number];
  area: number;
  confidence: number;
  description?: string;
}

export interface ChangeAnalysisResponse {
  before_image: SatelliteImage;
  after_image: SatelliteImage;
  changed_regions: ChangedRegion[];
  change_mask?: string;
  summary: string;
}

export interface ConstructionAnalysisResponse {
  candidate_regions: ChangedRegion[];
  summary: string;
  confidence: number;
  limitations: string[];
}

export interface Report {
  location: Location;
  date_before: string;
  date_after: string;
  imagery: string;
  summary: string;
  detected_changes: number;
  potential_construction_regions: number;
  key_regions: number[];
  confidence: 'High' | 'Medium' | 'Low';
  limitations: string[];
}

export interface AnalysisResult {
  answer: string
  confidence: number
  observations: string[]
  limitations: string[]
  regions?: ChangedRegion[]
}

export interface SuperResolutionResult {
  input_url: string
  output_url: string
  input_preview_url: string
  output_preview_url: string
  model: string
  scale: number
  input_width: number
  input_height: number
  output_width: number
  output_height: number
  input_resolution_m: number
  output_resolution_m: number
  processing_time_seconds: number
  metrics: { psnr?: number; ssim?: number } | null
  validation_message?: string
}