import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Regressão: eixos/séries/colunas no inspetor Elemento enchiam o painel e
 * “esvaziavam” o Design ao marcar série. Projeção completa só na aba Dados.
 */
describe("view projection vs format inspector", () => {
  it("Elemento usa mode=connection; Dados usa mode=full", () => {
    const element = readFileSync(
      resolve(__dirname, "./deck/ComunicadoElementInspector.tsx"),
      "utf8",
    );
    expect(element).toMatch(/VisualDataViewInspector[\s\S]*mode="connection"/);

    const data = readFileSync(resolve(__dirname, "./SelectedDataSidePanel.tsx"), "utf8");
    expect(data).toMatch(/VisualDataViewInspector[\s\S]*mode="full"/);
  });

  it("VisualDataViewInspector só monta editores de projeção em mode=full", () => {
    const source = readFileSync(resolve(__dirname, "./VisualDataViewInspector.tsx"), "utf8");
    expect(source).toContain('mode = "full"');
    expect(source).toContain("showProjectionEditors");
    expect(source).toMatch(
      /showProjectionEditors &&[\s\S]*ChartAxesProjectionEditor/,
    );
    expect(source).toMatch(
      /showProjectionEditors &&[\s\S]*TableColumnsMultiSelect/,
    );
  });
});
