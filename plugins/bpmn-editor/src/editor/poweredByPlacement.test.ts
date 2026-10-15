/**
 * G9-BRAND-1 — regressão da colisão marca bpmn.io × controles do canvas.
 *
 * A LICENSE do bpmn-js exige o watermark visível e não sobreposto —
 * removê-lo (display:none / DOM hack) é proibido. O contrato desta
 * suíte: o selo é REPOSICIONADO para fora da área dos controles
 * (bottom-left) via CSS escopado ao root canônico do produto, nunca
 * global nem escondido.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const CSS = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../styles.css"),
  "utf-8",
);

const block = (selector: string): string => {
  const idx = CSS.indexOf(selector + " {");
  if (idx < 0) return "";
  const start = idx + selector.length + 2;
  return CSS.slice(start, CSS.indexOf("}", start));
};

describe("G9-BRAND-1 — powered-by não intercepta controles do canvas", () => {
  it("regra do selo existe e está escopada ao root canônico", () => {
    expect(CSS).toContain(".dashboard-bpmn-modeler .bjs-powered-by");
  });

  it("selo é reposicionado para bottom-left, fora da área dos controles", () => {
    const rule = block(".dashboard-bpmn-modeler .bjs-powered-by");
    expect(rule).toContain("left:");
    expect(rule).toContain("right: auto");
    expect(rule).not.toContain("display: none");
    expect(rule).not.toContain("visibility: hidden");
    expect(rule).not.toContain("pointer-events: none");
  });

  it("nenhuma regra NÃO escopada toca .bjs-powered-by", () => {
    const unscoped = /(^|[},]\s*)\.bjs-powered-by\s*{/m;
    expect(CSS).not.toMatch(unscoped);
  });

  it("controles mantêm posição/z-index explícitos na área bottom-right", () => {
    const controls = block(".bpmnm-readonly-viewer__controls");
    expect(controls).toContain("position: absolute");
    expect(controls).toContain("right:");
    expect(controls).toContain("bottom:");
    expect(controls).toContain("z-index");
    const editorControls = block(".bpmnm-viewport-controls");
    expect(editorControls).toContain("z-index");
  });
});
