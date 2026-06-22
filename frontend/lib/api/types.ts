// Typed models mirroring the backend Pydantic schemas (app/schemas/*).

export type DocumentStatus =
  | "uploaded"
  | "queued"
  | "processing"
  | "completed"
  | "failed";

export type CitationType = "case" | "statute" | "regulation" | "unknown";

export type ValidationResultType =
  | "verified"
  | "suspicious"
  | "hallucinated"
  | "unverifiable";

export type FindingSeverity = "info" | "warning" | "error" | "critical";

export type SourceType = "case" | "statute" | "regulation";

export interface Finding {
  check: string;
  severity: FindingSeverity;
  passed: boolean;
  message: string;
}

export interface MatchedSource {
  id: string;
  source_type: SourceType;
  title: string;
  volume?: number | null;
  reporter?: string | null;
  page?: number | null;
  year?: number | null;
  court?: string | null;
  code?: string | null;
  section?: string | null;
}

export interface Validation {
  id: string;
  result: ValidationResultType;
  confidence: number;
  summary: string;
  findings: Finding[];
  matched_source?: MatchedSource | null;
}

export interface Citation {
  id: string;
  citation_type: CitationType;
  raw_text: string;
  normalized_text?: string | null;
  start_offset: number;
  end_offset: number;
  case_name?: string | null;
  volume?: number | null;
  reporter?: string | null;
  page?: number | null;
  pin_cite?: number | null;
  year?: number | null;
  court?: string | null;
  title_number?: number | null;
  code?: string | null;
  section?: string | null;
  validation?: Validation | null;
}

export interface DocumentRead {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  status: DocumentStatus;
  page_count?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentRead {
  citations: Citation[];
}

export interface DocumentList {
  items: DocumentRead[];
  total: number;
}

export interface DashboardStats {
  document_id: string;
  status: DocumentStatus;
  total_citations: number;
  verified: number;
  suspicious: number;
  hallucinated: number;
  unverifiable: number;
  flagged: number;
  verification_rate: number;
  average_confidence: number;
}

export interface ApiError {
  error: { code: string; message: string };
}
