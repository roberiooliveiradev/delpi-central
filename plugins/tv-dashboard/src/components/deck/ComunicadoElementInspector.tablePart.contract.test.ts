import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Regressão: Design/Layout da tabela sumiam com `selectedTablePart` (coluna),
 * deixando a sidebar vazia ao marcar/desmarcar colunas após foco no palco.
 *
 * Causa raiz: `selectTablePart` pedia aba `element` (inexistente para tabela) →
 * `panelFocus=element` escondia Design. Mitigação: mapear `element`→`tableDesign`.
 */
describe("ComunicadoElementInspector table block sections", () => {
  it("mantém seções Design/Layout mesmo com parte/coluna selecionada", () => {
    const source = readFileSync(resolve(__dirname, "./ComunicadoElementInspector.tsx"), "utf8");
    expect(source).toContain("keepTableBlockSections");
    expect(source).toContain("showTableBlockSections");
    expect(source).toContain("tablePanelFocus");
    expect(source).toMatch(
      /tablePanelFocus\s*=\s*[\s\S]*panelFocus === "element"\s*\?\s*"tableDesign"/,
    );
    expect(source).toMatch(
      /keepTableBlockSections\s*=\s*[\s\S]*tablePanelFocus === "tableDesign"[\s\S]*tablePanelFocus === "tableLayout"/,
    );
    expect(source).toMatch(
      /showTableBlockSections\s*=\s*[\s\S]*!selectedTablePart \|\| keepTableBlockSections/,
    );
  });

  it("mantém seções de gráfico na aba Elemento com parte selecionada", () => {
    const source = readFileSync(resolve(__dirname, "./ComunicadoElementInspector.tsx"), "utf8");
    expect(source).toContain("showChartBlockSections");
    expect(source).toMatch(
      /showChartBlockSections\s*=\s*[\s\S]*panelFocus === "element" \|\| !selectedChartPart/,
    );
  });

  it("mantém ChartViewOptionsInspector com parte selecionada (valor da meta / grade)", () => {
    const source = readFileSync(resolve(__dirname, "./ComunicadoElementInspector.tsx"), "utf8");
    expect(source).toContain("<ChartViewOptionsInspector pane={pane} omitSeries />");
    expect(source).not.toMatch(
      /!selectedChartPart\s*\?\s*<ChartViewOptionsInspector/,
    );
  });
});
