import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const page = readFileSync(join(dir, "ProcessesPage.tsx"), "utf8");
const browser = readFileSync(join(dir, "../processes/ProcessFolderBrowser.tsx"), "utf8");
const presentation = readFileSync(
  join(dir, "../processes/ProcessListPresentationControls.tsx"),
  "utf8",
);
const browseToggle = readFileSync(join(dir, "../processes/ProcessListBrowseToggle.tsx"), "utf8");

describe("ProcessesPage hero compacto", () => {
  it("concentra consulta e apresentação no PageHeader.children", () => {
    expect(page).toMatch(/<PageHeader[\s\S]*tm-processos-hero__query[\s\S]*<\/PageHeader>/);
    expect(page).toMatch(/tm-processos-hero__presentation/);
    expect(page).toMatch(/buildRootSectionPagePath/);
    expect(page).toMatch(/id="tm-proc-q"/);
    expect(page).toMatch(/id="tm-proc-list-status"/);
    expect(page).toMatch(/ProcessListBrowseToggle/);
    expect(page).toMatch(/ProcessListPresentationControls/);
    expect(page).toMatch(/parts=\{\["sort-field"\]\}/);
    expect(page).toMatch(/parts=\{\["sort-direction", "view-modes"\]\}/);
  });

  it("desativa controles duplicados no browser de resultados", () => {
    expect(page).toMatch(/hideBrowseToggle/);
    expect(page).toMatch(/hideListToolbar/);
    expect(page).not.toMatch(/filters=\{/);
    expect(page).not.toMatch(/DS_FILTERS_ROW_EXTENDED\}>\s*\n\s*<div className=\{DS_FILTER_BOX_WIDE\}/);
  });

  it("preserva criação, watch, busca e status", () => {
    expect(page).toMatch(/startCreate/);
    expect(page).toMatch(/useTransformometroCatalogWatch/);
    expect(page).toMatch(/buildProcessListQuery/);
    expect(page).toMatch(/searchQ/);
    expect(page).toMatch(/statusFilter/);
    expect(page).toMatch(/Novo processo/);
    expect(page).toMatch(/status === 403/);
  });

  it("reutiliza componentes compartilhados sem segunda toolbar genérica", () => {
    expect(browseToggle).toMatch(/PROCESSO_LIST_BROWSE_MODES/);
    expect(presentation).toMatch(/ProcessListPresentationPart/);
    expect(browser).toMatch(/ProcessListBrowseToggle/);
    expect(browser).toMatch(/onBrowseContextChange/);
    expect(browser).toMatch(/tm-processo-browser__results-meta/);
  });
});
