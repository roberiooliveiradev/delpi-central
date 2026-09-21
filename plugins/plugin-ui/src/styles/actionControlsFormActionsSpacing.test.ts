import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(__dirname, "action-controls.css"), "utf8");

describe("action-controls FormActions spacing", () => {
  it("define gap canônico de 24px no FormActions", () => {
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*\{[^}]*gap:\s*var\(--delpi-ui-form-actions-gap,\s*24px\)/,
    );
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*>\s*\.delpi-ui-action-btn\s*\+\s*\.delpi-ui-action-btn[\s\S]*?margin-inline-start:\s*0/,
    );
  });

  it("define margem superior canônica entre conteúdo e barra de ações", () => {
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*\{[^}]*margin-block-start:\s*var\(--delpi-ui-form-actions-block-start,\s*24px\)/,
    );
  });

  it("mobile ≤768 empilha FormActions em coluna full-width", () => {
    expect(css).toMatch(
      /@media\s*\(max-width:\s*768px\)\s*\{[\s\S]*?\.delpi-ui-form-actions[\s\S]*?flex-direction:\s*column/,
    );
    expect(css).toMatch(
      /@media\s*\(max-width:\s*768px\)\s*\{[\s\S]*?\.delpi-ui-form-actions\s*>\s*\*[\s\S]*?width:\s*100%/,
    );
    expect(css).toMatch(
      /@media\s*\(max-width:\s*768px\)\s*\{[\s\S]*?\.delpi-ui-form-actions\s+\.delpi-ui-help-tooltip--wrap[\s\S]*?width:\s*100%/,
    );
  });

  it("no hover o primary mantém fundo e ícone, sem o reset global do portal", () => {
    expect(css).toMatch(
      /\.delpi-ui-icon-btn--primary:hover:not\(:disabled\)[\s\S]*?background:\s*var\(--delpi-ui-accent/,
    );
    expect(css).toMatch(
      /\.delpi-ui-icon-btn--primary:hover:not\(:disabled\)[\s\S]*?color:\s*var\(--delpi-ui-on-accent,\s*#ffffff\)/,
    );
    expect(css).toMatch(
      /\.delpi-ui-action-btn--primary:hover:not\(:disabled\):not\(\.delpi-ui-action-btn--disabled\)[\s\S]*?background:\s*var\(--delpi-ui-accent/,
    );
  });

  it("desliga o visual nativo do botão para o tema do portal pintar o ícone", () => {
    expect(css).toMatch(/\.delpi-ui-action-btn\s*\{[^}]*appearance:\s*none/);
    expect(css).toMatch(/\.delpi-ui-icon-btn\s*\{[^}]*appearance:\s*none/);
    expect(css).toMatch(
      /\.delpi-ui-icon-btn--primary\s*\{[^}]*color:\s*var\(--delpi-ui-on-accent,\s*#ffffff\)/,
    );
    expect(css).toMatch(
      /:root\[data-theme="dark"\]\s*\.delpi-ui-icon-btn--primary[\s\S]*?color:\s*var\(--delpi-ui-on-accent,\s*#ffffff\)/,
    );
  });

  it("desktop FormActions base não usa coluna", () => {
    const baseBlock = css.match(/\.delpi-ui-form-actions\s*\{[^}]+\}/);
    expect(baseBlock?.[0] ?? "").not.toMatch(/flex-direction:\s*column/);
  });
});
