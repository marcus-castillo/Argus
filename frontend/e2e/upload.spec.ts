import { test, expect } from "@playwright/test";
import path from "node:path";

const SAMPLE = path.resolve(
  __dirname,
  "../../backend/seed/samples/demo_brief.txt",
);

test.describe("CiteCheck end-to-end", () => {
  test("home page loads with upload affordance", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /verify the citations/i }),
    ).toBeVisible();
    await expect(page.getByText(/drop a brief, motion, or memo/i)).toBeVisible();
  });

  test("upload a brief, wait for verification, see dashboard + download", async ({
    page,
  }) => {
    await page.goto("/");

    // Upload via the hidden file input.
    await page.setInputFiles('input[type="file"]', SAMPLE);

    // We are routed to the document detail page.
    await expect(page).toHaveURL(/\/documents\/[0-9a-f-]+/);

    // Wait for processing to complete and the dashboard to render.
    await expect(page.getByText("Total citations")).toBeVisible({
      timeout: 30_000,
    });

    // Expect at least one hallucinated and one verified citation in the table.
    await expect(page.getByText("Hallucinated").first()).toBeVisible();
    await expect(page.getByText("Verified").first()).toBeVisible();

    // Report download buttons are present.
    await expect(page.getByRole("link", { name: "PDF" })).toBeVisible();
    await expect(page.getByRole("link", { name: "CSV" })).toBeVisible();
    await expect(page.getByRole("link", { name: "JSON" })).toBeVisible();

    // Expanding a citation row reveals findings.
    await page.getByTestId("citation-row").first().click();
  });
});
