import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const cssPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "questionnaire.css",
);
const css = readFileSync(cssPath, "utf8");

/** Bloco de declarações de um seletor simples (sem chaves aninhadas). */
function declarationBlock(selectorPattern: RegExp): string {
  const match = css.match(selectorPattern);
  expect(match, `bloco ${selectorPattern}`).toBeTruthy();
  return match![1];
}

const lightBlock = declarationBlock(/\.delpi-ui-form-root\s*\{([^}]*)\}/);
const darkBlock = declarationBlock(
  /\.delpi-ui-form-root\[data-color-scheme="dark"\]\s*\{([^}]*)\}/,
);

// Tokens da UI-03 §3.2 — valor claro e escuro (inventário 16/11/2026).
const TOKEN_VALUES: Record<string, { light: string; dark: string }> = {
  "--delpi-ui-form-font": {
    light: '"Segoe UI", Inter, system-ui, -apple-system, sans-serif',
    dark: '"Segoe UI", Inter, system-ui, -apple-system, sans-serif',
  },
  "--delpi-ui-form-page-bg": { light: "#f3f4f6", dark: "#041b2e" },
  "--delpi-ui-form-band-bg": { light: "#0c6fb0", dark: "#003866" },
  "--delpi-ui-form-card-shadow": {
    light: "0 1px 2px rgba(16, 24, 40, 0.06)",
    dark: "0 1px 2px rgba(0, 0, 0, 0.35)",
  },
  "--delpi-ui-form-accent-text": { light: "#0a5a8f", dark: "#7fd3f5" },
  "--delpi-ui-form-tint": { light: "#eaf3fb", dark: "#103c55" },
  "--delpi-ui-form-border-soft": { light: "#d0d7de", dark: "#788792" },
  "--delpi-ui-form-input-bg": { light: "#ffffff", dark: "#061622" },
  "--delpi-ui-form-track": { light: "#e6eaef", dark: "#2c4354" },
  "--delpi-ui-form-warning-bg": { light: "#fff8e6", dark: "#273736" },
  "--delpi-ui-form-warning-border": { light: "#f0d58c", dark: "#6a6230" },
  "--delpi-ui-form-warning-text": { light: "#5c4400", dark: "#fde68a" },
  "--delpi-ui-form-logo-bg": { light: "transparent", dark: "#ffffff" },
  "--delpi-ui-surface": { light: "#ffffff", dark: "#0a2438" },
  "--delpi-ui-border": {
    light: "#e1e4e8",
    dark: "rgba(255, 255, 255, 0.14)",
  },
  "--delpi-ui-text": { light: "#1f2328", dark: "#f4f8fc" },
  "--delpi-ui-muted": { light: "#57606a", dark: "#b8c9d9" },
  "--delpi-ui-accent": { light: "#0c6fb0", dark: "#30b8ec" },
  "--delpi-ui-on-accent": { light: "#ffffff", dark: "#041b2e" },
  "--delpi-ui-control-border": { light: "#8c959f", dark: "#788792" },
  "--delpi-ui-danger": { light: "#b42318", dark: "#ff9d9d" },
  "--delpi-ui-success": { light: "#1a7f37", dark: "#2ecc71" },
  "--delpi-ui-focus-ring": {
    light: "0 0 0 3px #8fc3ea",
    dark: "0 0 0 3px #7fd3f5",
  },
};

function normalize(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

describe("questionnaire.css — contrato de tokens e escopo", () => {
  it("define todos os tokens da UI-03 §3.2 no bloco claro e no bloco dark", () => {
    const light = normalize(lightBlock);
    const dark = normalize(darkBlock);
    for (const [token, values] of Object.entries(TOKEN_VALUES)) {
      expect(light, `claro ${token}`).toContain(
        `${token}: ${normalize(values.light)}`,
      );
      expect(dark, `escuro ${token}`).toContain(
        `${token}: ${normalize(values.dark)}`,
      );
    }
  });

  it("declara color-scheme correspondente em cada bloco", () => {
    expect(normalize(lightBlock)).toContain("color-scheme: light");
    expect(normalize(darkBlock)).toContain("color-scheme: dark");
  });

  it("não contém seletor global nem !important", () => {
    expect(css).not.toMatch(/!important/);
    expect(css).not.toMatch(/:root[\s,{]/);
    expect(css).not.toMatch(/(^|[\s,{])html[\s,{]/m);
    expect(css).not.toMatch(/(^|[\s,{])body[\s,{]/m);
    expect(css).not.toMatch(/(^|[\s,{])\*[\s,{]/m);
  });

  it("não redeclara o chrome de form-actions (namespace reservado do kit)", () => {
    expect(css).not.toMatch(/form-actions/);
  });

  it("classes novas usam só var(--delpi-ui-*) para cor/sombra/borda", () => {
    // Declarações cor-de-fundo/borda/sombra/fill/stroke/caret fora dos blocos
    // de token devem referenciar tokens — literais só nos valores permitidos.
    const COLORISH =
      /^(color|background|background-color|box-shadow|fill|stroke|caret-color|outline|outline-color|border|border-color|border-top-color|border-right-color|border-bottom-color|border-left-color)$/;
    const ALLOWED_LITERAL =
      /^(none|transparent|currentcolor|inherit|initial|unset|0|auto)$/i;

    // Remove os blocos de tokens (raiz claro/escuro) — lá os literais são válidos.
    const withoutTokenBlocks = css
      .replace(/\.delpi-ui-form-root\s*\{[^}]*\}/, "")
      .replace(
        /\.delpi-ui-form-root\[data-color-scheme="dark"\]\s*\{[^}]*\}/,
        "",
      );

    const rulePattern = /([^{}]+)\{([^}]*)\}/g;
    const violations: string[] = [];
    let rule: RegExpExecArray | null;
    while ((rule = rulePattern.exec(withoutTokenBlocks)) !== null) {
      const selector = rule[1].trim();
      if (selector.startsWith("@")) continue;
      for (const decl of rule[2].split(";")) {
        const [prop, ...rest] = decl.split(":");
        if (!rest.length) continue;
        const property = prop.trim();
        const value = rest.join(":").trim();
        if (property.startsWith("--")) continue;
        if (!COLORISH.test(property)) continue;
        if (/var\(/.test(value)) continue;
        if (ALLOWED_LITERAL.test(value)) continue;
        violations.push(`${selector} { ${property}: ${value} }`);
      }
    }
    expect(violations).toEqual([]);
  });

  it("P3: classes novas de resposta existem e só usam tokens de cor", () => {
    const REQUIRED_SELECTORS = [
      ".delpi-ui-form-answer-stack",
      ".delpi-ui-form-scale",
      ".delpi-ui-form-scale__options-row",
      ".delpi-ui-form-scale__options",
      ".delpi-ui-form-scale__options--dense",
      ".delpi-ui-form-scale__option",
      ".delpi-ui-form-scale__input",
      ".delpi-ui-form-scale__ends",
      ".delpi-ui-form-scale__caption",
      ".delpi-ui-form-scale__divider",
      ".delpi-ui-form-scale--invalid",
      ".delpi-ui-form-na",
      ".delpi-ui-form-na__indicator",
      ".delpi-ui-form-na--invalid",
      ".delpi-ui-form-textanswer",
      ".delpi-ui-form-textanswer__label",
      ".delpi-ui-form-textanswer__control--textarea",
    ];
    for (const selector of REQUIRED_SELECTORS) {
      expect(css, selector).toContain(selector);
    }
  });

  it("R6: a pilha da resposta tem gap 12 px (estreito) e 14 px (≥600)", () => {
    const stackBlock = declarationBlock(
      /\.delpi-ui-form-answer-stack\s*\{([^}]*)\}/,
    );
    expect(normalize(stackBlock)).toContain("gap: 12px");
    const stackMedia = css.match(
      /\.delpi-ui-form-answer-stack\s*\{[^}]*gap:\s*14px[^}]*\}/,
    );
    expect(stackMedia).toBeTruthy();
  });
});
