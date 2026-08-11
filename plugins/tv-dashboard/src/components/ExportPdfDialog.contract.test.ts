import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("ExportPdfDialog contract", () => {
  it("usa HostContainedDialog e escopos programação/seleção/slide atual", () => {
    const source = readFileSync(join(here, "ExportPdfDialog.tsx"), "utf8");
    expect(source).toContain("HostContainedDialog");
    expect(source).toContain('title="Exportar PDF"');
    expect(source).toContain('setScope("playlist")');
    expect(source).toContain('setScope("current")');
    expect(source).toContain('setScope("selected")');
    expect(source).toContain("selectedSlideCount");
    expect(source).toContain("pixelRatio");
    expect(source).toContain("Gerar PDF");
  });

  it("tile PDF da ribbon abre o diálogo (não exporta A4 direto)", () => {
    const ribbon = readFileSync(join(here, "SlideCurrentRibbon.tsx"), "utf8");
    expect(ribbon).toContain("onExportPdf");
    expect(ribbon).toContain("exportPdf");
    expect(ribbon).not.toContain("página A4");

    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");
    expect(page).toContain("ExportPdfDialog");
    expect(page).toContain("setExportPdfOpen(true)");
    expect(page).toContain("exportActivePlaylistSlidesToPdf");
    expect(page).toContain("designSize");
  });
});
