import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("media library delete contract", () => {
  it("modal expõe exclusão com confirmação e client API", () => {
    const modal = readFileSync(join(here, "MediaLibraryModal.tsx"), "utf8");
    const api = readFileSync(join(here, "../api/tvDashboardApi.ts"), "utf8");
    const css = readFileSync(join(here, "../index.css"), "utf8");

    expect(modal).toContain("deletePlaylistMedia");
    expect(modal).toContain("td-media-library__delete");
    expect(modal).toContain("window.confirm");
    expect(modal).toContain("handleDelete");
    expect(api).toContain("export async function deletePlaylistMedia");
    expect(api.match(/export async function deletePlaylistMedia/g)?.length).toBe(1);
    expect(css).toMatch(/\.td-media-library__delete\s*\{/);
  });
});

describe("media library layout contract", () => {
  it("abre com caixa viewport-fixa (não td-modal--wide shrink-to-fit)", () => {
    const modal = readFileSync(join(here, "MediaLibraryModal.tsx"), "utf8");
    const css = readFileSync(join(here, "../index.css"), "utf8");

    expect(modal).toContain('className="td-modal--media-library"');
    expect(modal).not.toMatch(/HostContainedDialog[^>]*className="td-modal--wide"/);
    expect(css).toMatch(/\.td-modal\.td-modal--media-library/);
    expect(css).toMatch(/min-width:\s*min\(980px/);
    expect(css).toMatch(/height:\s*min\(85dvh/);
    expect(css).toMatch(
      /\.td-modal--media-library\s+\.td-media-library__grid\s*\{[^}]*align-content:\s*start/s,
    );
    expect(css).toContain("@media (max-width: 768px)");
    expect(css).toMatch(/\.td-modal--media-library\s*\{[^}]*90dvh/s);
  });
});
