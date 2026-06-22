"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/result-badge";
import { formatBytes, formatDate } from "@/lib/utils";
import type { DocumentRead } from "@/lib/api/types";

export function DocumentsTable({ documents }: { documents: DocumentRead[] }) {
  if (documents.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No documents yet. Upload a filing to get started.
      </p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Filename</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Uploaded</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((d) => (
          <TableRow key={d.id} data-testid="document-row">
            <TableCell>
              <Link
                href={`/documents/${d.id}`}
                className="font-medium text-primary hover:underline"
              >
                {d.filename}
              </Link>
            </TableCell>
            <TableCell>
              <StatusBadge status={d.status} />
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatBytes(d.size_bytes)}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatDate(d.created_at)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
