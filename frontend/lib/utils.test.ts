import { describe, expect, it } from "vitest";
import { cn, formatBytes, formatPercent } from "./utils";

describe("utils", () => {
  it("cn merges and dedupes tailwind classes", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-sm", false && "hidden", "font-bold")).toBe(
      "text-sm font-bold",
    );
  });

  it("formatBytes is human readable", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });

  it("formatPercent renders one decimal", () => {
    expect(formatPercent(0.5)).toBe("50.0%");
    expect(formatPercent(0.8312)).toBe("83.1%");
  });
});
