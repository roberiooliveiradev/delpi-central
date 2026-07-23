import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Dual-class DelpiKpiCard value = `.delpi-kpi-card__value` + `.delpi-ui-kpi-value`.
 * departmental-kpi.css (importado depois) define `overflow:hidden` + ellipsis no valor;
 * sem override com !important, os handles de parte ficam clipados (só ponta do adjust).
 */
describe("KPI part chrome overflow (valor selecionado)", () => {
  const kpiCardCss = readFileSync(resolve(__dirname, "./kpi-card.css"), "utf8");
  const departmentalCss = readFileSync(resolve(__dirname, "./departmental-kpi.css"), "utf8");
  const stylesEntry = readFileSync(resolve(__dirname, "../styles.css"), "utf8");

  it("departmental-kpi ainda clipa .delpi-ui-kpi-value (ellipsis de dashboard)", () => {
    expect(departmentalCss).toMatch(
      /\.delpi-ui-kpi-value\s*\{[^}]*overflow:\s*hidden/s,
    );
  });

  it("kpi-card força overflow visible no valor com chrome de parte", () => {
    expect(kpiCardCss).toContain(".delpi-ui-kpi-value.delpi-kpi-part--resizable");
    expect(kpiCardCss).toContain(".delpi-kpi-card__value.delpi-kpi-part--resizable");
    expect(kpiCardCss).toMatch(
      /\.delpi-ui-kpi-value\.delpi-kpi-part--resizable\s*\{[^}]*overflow:\s*visible\s*!important/s,
    );
  });

  it("abre overflow no card dual-class quando há parte selecionada", () => {
    expect(kpiCardCss).toContain(
      ".delpi-ui-card.delpi-ui-kpi-card:has(.delpi-kpi-part--resizable)",
    );
    expect(kpiCardCss).toMatch(/overflow:\s*visible\s*!important/);
  });

  it("styles.css importa kpi-card antes de departmental-kpi (cascade documentada)", () => {
    const kpiIdx = stylesEntry.indexOf("./styles/kpi-card.css");
    const deptIdx = stylesEntry.indexOf("./styles/departmental-kpi.css");
    expect(kpiIdx).toBeGreaterThan(-1);
    expect(deptIdx).toBeGreaterThan(kpiIdx);
  });
});
