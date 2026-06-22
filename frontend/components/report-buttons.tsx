"use client";

import { Download } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";

export function ReportButtons({ documentId }: { documentId: string }) {
  const formats: Array<"pdf" | "csv" | "json"> = ["pdf", "csv", "json"];
  return (
    <div className="flex flex-wrap gap-2">
      {formats.map((fmt) => (
        <a
          key={fmt}
          href={api.reportUrl(documentId, fmt)}
          target="_blank"
          rel="noopener noreferrer"
          download
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          <Download className="h-4 w-4" />
          {fmt.toUpperCase()}
        </a>
      ))}
    </div>
  );
}
