"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ResultBadge } from "@/components/result-badge";
import { formatPercent } from "@/lib/utils";
import type { Citation, FindingSeverity } from "@/lib/api/types";

const SEVERITY_VARIANT: Record<
  FindingSeverity,
  "muted" | "warning" | "destructive"
> = {
  info: "muted",
  warning: "warning",
  error: "destructive",
  critical: "destructive",
};

export function CitationsTable({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No citations were extracted from this document.
      </p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-8" />
          <TableHead>Citation</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Result</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Supporting source</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {citations.map((c) => (
          <CitationRow key={c.id} citation={c} />
        ))}
      </TableBody>
    </Table>
  );
}

function CitationRow({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const v = citation.validation;
  const findings = v?.findings ?? [];
  return (
    <>
      <TableRow
        className="cursor-pointer"
        onClick={() => setOpen((o) => !o)}
        data-testid="citation-row"
      >
        <TableCell>
          {open ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </TableCell>
        <TableCell className="font-medium">{citation.raw_text}</TableCell>
        <TableCell>
          <Badge variant="outline">{citation.citation_type}</Badge>
        </TableCell>
        <TableCell>
          {v ? <ResultBadge result={v.result} /> : <Badge variant="muted">—</Badge>}
        </TableCell>
        <TableCell>{v ? formatPercent(v.confidence) : "—"}</TableCell>
        <TableCell className="text-muted-foreground">
          {v?.matched_source?.title ?? "—"}
        </TableCell>
      </TableRow>
      {open && (
        <TableRow>
          <TableCell />
          <TableCell colSpan={5}>
            <div className="space-y-2 py-1">
              {v?.summary && (
                <p className="text-sm text-muted-foreground">{v.summary}</p>
              )}
              <ul className="space-y-1">
                {findings.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={SEVERITY_VARIANT[f.severity]}>
                      {f.check}
                    </Badge>
                    <span className={f.passed ? "text-foreground" : "text-foreground"}>
                      {f.message}
                    </span>
                  </li>
                ))}
                {findings.length === 0 && (
                  <li className="text-sm text-muted-foreground">
                    No detailed findings recorded.
                  </li>
                )}
              </ul>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
