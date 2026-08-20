import { describe, expect, it } from "vitest";

import { formatRefreshedAt } from "./formatRefreshedAt";

describe("formatRefreshedAt", () => {
  it("returns dash when empty", () => {
    expect(formatRefreshedAt(null)).toBe("—");
    expect(formatRefreshedAt("")).toBe("—");
  });

  it("formats a valid ISO timestamp", () => {
    const formatted = formatRefreshedAt("2026-08-19T22:00:00.000Z");
    expect(formatted).toMatch(/\d{2}\/\d{2}\/2026/);
  });
});
