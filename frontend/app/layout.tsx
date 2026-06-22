import type { Metadata } from "next";
import Link from "next/link";
import { Scale } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "CiteCheck — Legal Citation Validator",
  description:
    "Extract, verify, and flag hallucinated legal citations in briefs and motions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
        <header className="border-b border-border">
          <div className="mx-auto flex max-w-6xl items-center gap-2 px-6 py-4">
            <Link href="/" className="flex items-center gap-2">
              <Scale className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">CiteCheck</span>
            </Link>
            <span className="ml-2 rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              Legal Citation Validator
            </span>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl px-6 py-8 text-xs text-muted-foreground">
          CiteCheck verifies citations against a reference corpus. Always confirm
          authority before filing.
        </footer>
      </body>
    </html>
  );
}
