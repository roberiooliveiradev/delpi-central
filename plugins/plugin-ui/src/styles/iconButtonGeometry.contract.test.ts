import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "action-controls.css"),
  "utf8",
);

describe("action-controls.css — geometria quadrada do IconButton", () => {
  const block = () => {
    /* bloco até o fechamento de regra no início de linha — o comentário
     * interno contém `{ min-width: 0 }` literal. */
    const match = css.match(/\.delpi-ui-icon-btn\s*\{([\s\S]*?)\n\}/);
    expect(match).toBeTruthy();
    return match![1];
  };

  it("declara largura e altura fixas de 36px (contrato quadrado)", () => {
    /* Regressão HELPDESK-UXV3-FILTERX-GEOMETRY: regras de consumidor
     * `wrap > * { min-width: 0 }` zeravam o piso e o botão encolhia a
     * ~18px (largura do SVG + borda). Com width/height fixas +
     * flex-shrink:0 o componente é autoprotegido. */
    const b = block();
    expect(b).toMatch(/width:\s*36px/);
    expect(b).toMatch(/height:\s*36px/);
    expect(b).toMatch(/min-width:\s*36px/);
    expect(b).toMatch(/min-height:\s*36px/);
    expect(b).toMatch(/flex-shrink:\s*0/);
  });

  it("mantém ícone centrado (inline-flex + center)", () => {
    const b = block();
    expect(b).toMatch(/display:\s*inline-flex/);
    expect(b).toMatch(/align-items:\s*center/);
    expect(b).toMatch(/justify-content:\s*center/);
  });
});
