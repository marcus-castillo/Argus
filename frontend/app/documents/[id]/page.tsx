"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardCards } from "@/components/dashboard-cards";
import { CitationsTable } from "@/components/citations-table";
import { ReportButtons } from "@/components/report-buttons";
import { StatusBadge } from "@/components/result-badge";
import { api } from "@/lib/api/client";
import type { DashboardStats, DocumentDetail } from "@/lib/api/types";

const ACTIVE_STATUSES = new Set(["uploaded", "queued", "processing"]);

export default function DocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([
        api.getDocument(id),
        api.getDashboard(id),
      ]);
      setDoc(d);
      setStats(s);
      setError(null);
      return d.status;
    } catch {
      setError("Could not load this document.");
      return "failed" as const;
    }
  }, [id]);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      const status = await load();
      if (active && ACTIVE_STATUSES.has(status)) {
        timer = setTimeout(tick, 2000);
      }
    };
    void tick();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [load]);

  if (error) {
    return (
      <div className="space-y-4">
        <BackLink />
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (!doc || !stats) {
    return (
      <div className="space-y-4">
        <BackLink />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }

  const processing = ACTIVE_STATUSES.has(doc.status);

  return (
    <div className="space-y-6">
      <BackLink />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{doc.filename}</h1>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge status={doc.status} />
            {doc.page_count != null && (
              <span className="text-xs text-muted-foreground">
                {doc.page_count} page(s)
              </span>
            )}
          </div>
        </div>
        {doc.status === "completed" && <ReportButtons documentId={doc.id} />}
      </div>

      {doc.status === "failed" && doc.error_message && (
        <Card>
          <CardContent className="pt-6 text-sm text-destructive">
            Processing failed: {doc.error_message}
          </CardContent>
        </Card>
      )}

      {processing ? (
        <Card>
          <CardContent className="flex items-center gap-2 pt-6 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Extracting and verifying citations…
          </CardContent>
        </Card>
      ) : (
        <>
          <DashboardCards stats={stats} />
          <Card>
            <CardHeader>
              <CardTitle>Citations</CardTitle>
            </CardHeader>
            <CardContent>
              <CitationsTable citations={doc.citations} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function BackLink() {
  return (
    <Button asChild variant="ghost" size="sm">
      <Link href="/" className="text-muted-foreground">
        <ArrowLeft className="h-4 w-4" />
        All documents
      </Link>
    </Button>
  );
}
