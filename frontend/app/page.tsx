"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadForm } from "@/components/upload-form";
import { DocumentsTable } from "@/components/documents-table";
import { api } from "@/lib/api/client";
import type { DocumentRead } from "@/lib/api/types";

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data.items);
      setError(null);
    } catch {
      setError("Could not reach the CiteCheck API.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Verify the citations in your filing
        </h1>
        <p className="text-sm text-muted-foreground">
          Upload a brief, motion, or memorandum. CiteCheck extracts every case,
          statutory, and regulatory citation and flags anything suspicious or
          hallucinated.
        </p>
      </section>

      <UploadForm onUploaded={load} />

      <Card>
        <CardHeader>
          <CardTitle>Recent documents</CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <DocumentsTable documents={documents} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
