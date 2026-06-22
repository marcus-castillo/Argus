"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { UploadCloud, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, ApiClientError } from "@/lib/api/client";

const ACCEPT = ".pdf,.docx,.txt,.md";

export function UploadForm({ onUploaded }: { onUploaded?: () => void }) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const doc = await api.uploadDocument(file);
      onUploaded?.();
      router.push(`/documents/${doc.id}`);
    } catch (e) {
      setError(
        e instanceof ApiClientError ? e.message : "Upload failed. Try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files?.[0];
            if (file) void handleFile(file);
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
            dragging ? "border-primary bg-primary/5" : "border-border"
          }`}
        >
          {busy ? (
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          ) : (
            <UploadCloud className="h-8 w-8 text-muted-foreground" />
          )}
          <div>
            <p className="text-sm font-medium">
              {busy ? "Uploading…" : "Drop a brief, motion, or memo here"}
            </p>
            <p className="text-xs text-muted-foreground">
              PDF, DOCX, or plain text — click to browse
            </p>
          </div>
          <Button type="button" variant="outline" size="sm" disabled={busy}>
            Choose file
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
              e.target.value = "";
            }}
          />
        </div>
        {error && (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
