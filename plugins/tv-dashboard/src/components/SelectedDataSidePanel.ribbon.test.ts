import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Contrato da ribbon Dados (redesign): grupos reais colapsáveis em vez de
 * painel embutido — o inspector completo vive só no painel lateral e a
 * faixa nunca renderiza inspector/onboarding (vazava sobre o filmstrip).
 */
describe("Data ribbon contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const source = readFileSync(join(base, "./SelectedDataSidePanel.tsx"), "utf8");
  const ribbon = readFileSync(join(base, "./ComunicadoDataRibbon.tsx"), "utf8");
  const chrome = readFileSync(join(base, "./DeckEditorChrome.tsx"), "utf8");

  it("ribbon usa grupos DeckRibbonGroup estáveis, sem painel embutido", () => {
    // Sem o painel compacto legado — conteúdo da faixa é só grupos + flyouts.
    expect(ribbon).not.toMatch(/SelectedDataSidePanel/);
    expect(ribbon).not.toMatch(/overflowEnabled=\{false\}/);
    expect(ribbon).toMatch(/DeckRibbonGroup/);
    for (const groupId of [
      "data-source",
      "data-field",
      "data-period",
      "data-refresh",
      "data-expression",
      "data-more",
    ]) {
      expect(ribbon).toContain(`groupId="${groupId}"`);
    }
    // Flyouts canônicos ancorados — nunca inspector inline na faixa.
    expect(ribbon).toMatch(/DeckRibbonTilePopover/);
    expect(ribbon).not.toMatch(/VisualDataViewInspector/);
    expect(ribbon).not.toMatch(/td-deck-inspector__onboarding/);
  });

  it("painel lateral não tem mais branch de ribbon (sem dead code)", () => {
    expect(source).not.toMatch(/isRibbon/);
    expect(source).not.toMatch(/layout="ribbon"/);
  });

  it("ao abrir aba Dados, ribbon força o painel lateral", () => {
    expect(ribbon).toMatch(/setDataPanelOpen\(true\)/);
    expect(ribbon).toMatch(/setSelectionPanelTab\("data"\)/);
  });

  it("hydrate do painel Dados usa plan idempotente (não fingerprint de result.changed)", () => {
    expect(source).toMatch(/planHydrateBindingsApply/);
    expect(source).toMatch(/commitHydrateBindingsApplyPlan/);
    expect(source).not.toMatch(/hydratedFpRef/);
    expect(source).not.toMatch(/result\.changed/);
  });

  it("ribbon não reage à identidade do objeto selected (só id/tipo)", () => {
    expect(ribbon).toMatch(/selectedId/);
    expect(ribbon).toMatch(/selectedType/);
    expect(ribbon).not.toMatch(/\}, \[selected,/);
  });

  it("aba Dados usa densidade band (não fit)", () => {
    // Densidade estável em todas as abas — evita reflow do palco ao abrir Dados.
    expect(chrome).toMatch(/function ribbonDensityFor\([^)]*\):\s*"band"\s*\|\s*"fit"/);
    expect(chrome).toMatch(/return "band"/);
    expect(chrome).not.toMatch(/tab === "element" \? "fit"/);
  });
});
