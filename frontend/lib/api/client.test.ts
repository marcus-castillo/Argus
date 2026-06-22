import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiClientError } from "./client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("builds report URLs for each format", () => {
    expect(api.reportUrl("abc", "pdf")).toContain("/documents/abc/report.pdf");
    expect(api.reportUrl("abc", "csv")).toContain("/documents/abc/report.csv");
    expect(api.reportUrl("abc", "json")).toContain("/documents/abc/report.json");
  });

  it("parses successful JSON responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ items: [], total: 0 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const result = await api.listDocuments();
    expect(result.total).toBe(0);
  });

  it("throws ApiClientError with structured error body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            error: { code: "validation_error", message: "Bad file" },
          }),
          { status: 422 },
        ),
      ),
    );
    await expect(
      api.uploadDocument(new File(["x"], "x.exe")),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 422,
      code: "validation_error",
      message: "Bad file",
    });
  });

  it("surfaces ApiClientError instance", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("nope", { status: 500 })),
    );
    const err = await api.getDashboard("missing").catch((e) => e);
    expect(err).toBeInstanceOf(ApiClientError);
    expect(err.status).toBe(500);
  });
});
