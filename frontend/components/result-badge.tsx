import { Badge } from "@/components/ui/badge";
import type { DocumentStatus, ValidationResultType } from "@/lib/api/types";

const RESULT_MAP: Record<
  ValidationResultType,
  { label: string; variant: "success" | "warning" | "destructive" | "muted" }
> = {
  verified: { label: "Verified", variant: "success" },
  suspicious: { label: "Suspicious", variant: "warning" },
  hallucinated: { label: "Hallucinated", variant: "destructive" },
  unverifiable: { label: "Unverifiable", variant: "muted" },
};

export function ResultBadge({ result }: { result: ValidationResultType }) {
  const { label, variant } = RESULT_MAP[result];
  return <Badge variant={variant}>{label}</Badge>;
}

const STATUS_MAP: Record<
  DocumentStatus,
  { label: string; variant: "success" | "warning" | "destructive" | "muted" | "secondary" }
> = {
  uploaded: { label: "Uploaded", variant: "muted" },
  queued: { label: "Queued", variant: "secondary" },
  processing: { label: "Processing", variant: "warning" },
  completed: { label: "Completed", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const { label, variant } = STATUS_MAP[status];
  return <Badge variant={variant}>{label}</Badge>;
}
