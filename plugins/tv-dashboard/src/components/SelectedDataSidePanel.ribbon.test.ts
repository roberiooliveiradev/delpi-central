import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Regressão: ribbon Dados não monta VisualDataViewInspector / onboarding —
 * o bloco alto vazava sobre o filmstrip (slides «Personalizado»).
 */
describe("SelectedDataSidePanel ribbon contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const source = readFileSync(join(base, "./SelectedDataSidePanel.tsx"), "utf8");
  const ribbon = readFileSync(join(base, "./ComunicadoDataRibbon.tsx"), "utf8");
  const chrome = readFileSync(join(base, "./DeckEditorChrome.tsx"), "utf8");

  it("ribbon retorna cedo com toolbar compacta, sem VisualDataViewInspector", () => {
    const ribbonBranch = source.slice(source.indexOf("if (isRibbon)"));
    const beforePane = ribbonBranch.slice(0, ribbonBranch.indexOf("if (showCatalog)"));
    expect(beforePane).toMatch(/td-deck-ribbon__panel--dados-compact/);
    expect(beforePane).not.toMatch(/VisualDataViewInspector/);
    expect(beforePane).not.toMatch(/td-deck-inspector__onboarding/);
    expect(beforePane).toMatch(/Abrir catálogo de fontes/);
  });

  it("ao abrir aba Dados, ribbon força o painel lateral", () => {
    expect(ribbon).toMatch(/setDataPanelOpen\(true\)/);
    expect(ribbon).toMatch(/setSelectionPanelTab\("data"\)/);
  });

  it("aba Dados usa densidade band (não fit)", () => {
    expect(chrome).toMatch(/tab === "element" \? "fit" : "band"/);
  });
});
