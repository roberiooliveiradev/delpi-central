import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("preview parity=tv contract", () => {
  it("PlaylistPreviewPage pede parity=tv; editor não força no getPreviewPayload default", () => {
    const page = readFileSync(join(here, "PlaylistPreviewPage.tsx"), "utf8");
    const api = readFileSync(join(here, "../api/tvDashboardApi.ts"), "utf8");
    expect(page).toContain('parity: "tv"');
    expect(api).toContain('params.set("parity", "tv")');
  });
});
