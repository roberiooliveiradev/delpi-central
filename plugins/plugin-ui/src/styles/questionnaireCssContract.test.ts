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
  "--delpi-ui-form-footer-shadow": {
    light: "0 -4px 12px rgba(16, 24, 40, 0.08)",
    dark: "0 -4px 12px rgba(0, 0, 0, 0.4)",
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

  it("P4: classes novas de ação/fechamento existem", () => {
    const REQUIRED_SELECTORS = [
      ".delpi-ui-form-scale__main",
      ".delpi-ui-form-scale--ends-above",
      ".delpi-ui-form-button",
      ".delpi-ui-form-button--primary",
      ".delpi-ui-form-button--secondary",
      ".delpi-ui-form-button--full",
      ".delpi-ui-form-step-footer",
      ".delpi-ui-form-step-footer__message",
      ".delpi-ui-form-step-footer__actions",
      ".delpi-ui-form-step-footer__next",
      ".delpi-ui-form-notice",
      ".delpi-ui-form-notice--warning",
      ".delpi-ui-form-notice--info",
      ".delpi-ui-form-review__head",
      ".delpi-ui-form-review__title",
      ".delpi-ui-form-review__edit",
      ".delpi-ui-form-review__rows",
      ".delpi-ui-form-review__row",
      ".delpi-ui-form-review__row--muted",
      ".delpi-ui-form-review__row--block",
      ".delpi-ui-form-result__inner",
      ".delpi-ui-form-result__circle",
      ".delpi-ui-form-result__title",
      ".delpi-ui-form-result__message",
      ".delpi-ui-form-result__hint",
    ];
    for (const selector of REQUIRED_SELECTORS) {
      expect(css, selector).toContain(selector);
    }
  });

  it("P4: FormButton é escopado na raiz do kit — vence ActionButton por especificidade", () => {
    // §8.7: a sobrescrita do ActionButton não pode depender da ordem dos
    // @import em styles.css — os seletores do FormButton DEVEM carregar a
    // raiz `.delpi-ui-form-root` (especificidade 0-2-0 > 0-1-0).
    const SCOPED_SELECTORS = [
      /\.delpi-ui-form-root\s+\.delpi-ui-form-button\s*\{/,
      /\.delpi-ui-form-root\s+\.delpi-ui-form-button--primary\s*\{/,
      /\.delpi-ui-form-root\s+\.delpi-ui-form-button--secondary\s*\{/,
      /\.delpi-ui-form-root\s+\.delpi-ui-form-button:focus-visible\s*\{/,
      /\.delpi-ui-form-root\s+\.delpi-ui-form-button--full\s*\{/,
    ];
    for (const pattern of SCOPED_SELECTORS) {
      expect(css, String(pattern)).toMatch(pattern);
    }
    // Nenhum seletor de form-button desescopado (perderia para a ordem).
    const unscoped = css.match(
      /(^|\})\s*\.delpi-ui-form-button[^{]*\{/g,
    );
    for (const rule of unscoped ?? []) {
      expect(rule).toMatch(/\.delpi-ui-form-root\s/);
    }
    // E nunca !important (já coberto pelo teste global, reforçado aqui).
    expect(css).not.toMatch(/!important/);
  });

  it("P4: rodapé fixo só abaixo de 600 px (sticky + static no media)", () => {
    const footerBlock = declarationBlock(
      /\.delpi-ui-form-step-footer\s*\{([^}]*)\}/,
    );
    const footer = normalize(footerBlock);
    expect(footer).toContain("position: sticky");
    expect(footer).toContain("bottom: 0");
    expect(footer).toContain("margin: 8px -16px 0");
    expect(footer).toContain(
      "border-top: 1px solid var(--delpi-ui-border)",
    );
    expect(footer).toContain(
      "box-shadow: var(--delpi-ui-form-footer-shadow)",
    );
    const mediaFooter = css.match(
      /@media[^{]*min-width:\s*600px[^}]*\}[^@]*\.delpi-ui-form-step-footer\s*\{([^}]*)\}/,
    ) ??
      css.match(/\.delpi-ui-form-step-footer\s*\{[^}]*position:\s*static[^}]*\}/);
    expect(mediaFooter).toBeTruthy();
    expect(normalize(mediaFooter![1] ?? mediaFooter![0])).toContain(
      "position: static",
    );
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

  it("P6.1 R22: legend da pergunta flutua para dentro do cartão (sem entalhe na borda)", () => {
    const legendBlock = declarationBlock(
      /\.delpi-ui-form-question__legend\s*\{([^}]*)\}/,
    );
    expect(normalize(legendBlock)).toContain("float: left");
    expect(normalize(legendBlock)).toContain("width: 100%");
    expect(normalize(legendBlock)).toContain("padding: 0");
  });

  it("P6.1 R21: variante tall ≥600 px usa faixa 220 e sobreposição 160 (sem !important)", () => {
    const media = css.match(
      /@media\s*\(min-width:\s*600px\)\s*\{([\s\S]*?)\n\}/,
    );
    expect(media, "bloco @media 600px").toBeTruthy();
    const inner = media![1];
    const tallBand = inner.match(
      /\.delpi-ui-form-page--band-tall\s+\.delpi-ui-form-page__band\s*\{([^}]*)\}/,
    );
    expect(tallBand, "faixa tall dentro do media").toBeTruthy();
    expect(normalize(tallBand![1])).toContain("height: 220px");
    const tallColumn = inner.match(
      /\.delpi-ui-form-page--band-tall\s+\.delpi-ui-form-page__column\s*\{([^}]*)\}/,
    );
    expect(tallColumn, "coluna tall dentro do media").toBeTruthy();
    expect(normalize(tallColumn![1])).toContain("margin-top: -160px");
    expect(inner).not.toContain("!important");
  });

  it("P6.2 R25: selo do logo tem a mesma caixa nos dois temas — só o fundo muda", () => {
    const logoBlock = declarationBlock(/\.delpi-ui-form-logo\s*\{([^}]*)\}/);
    expect(normalize(logoBlock)).toContain("padding: 6px 10px");
    expect(normalize(logoBlock)).toContain("border-radius: 8px");
    expect(normalize(logoBlock)).toContain(
      "background: var(--delpi-ui-form-logo-bg)",
    );
    const darkLogo = css.match(
      /\.delpi-ui-form-root\[data-color-scheme="dark"\]\s+\.delpi-ui-form-logo\s*\{([^}]*)\}/,
    );
    // Se existir regra do logo no escuro, só pode declarar cor/fundo.
    if (darkLogo) {
      const props = [...darkLogo[1].matchAll(/([a-zA-Z-]+)\s*:/g)].map(
        (m) => m[1].toLowerCase(),
      );
      for (const prop of props) {
        expect(["background", "background-color"]).toContain(prop);
      }
    }
  });

  it("P6.2 R25: nenhum bloco do tema escuro declara geometria — só cor, sombra e color-scheme", () => {
    const GEOMETRY = new Set([
      "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
      "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
      "width", "height", "min-width", "min-height", "max-width", "max-height",
      "top", "right", "bottom", "left", "inset", "inset-block", "inset-inline",
      "gap", "row-gap", "column-gap",
      "border", "border-width", "border-top-width", "border-right-width",
      "border-bottom-width", "border-left-width", "border-radius",
      "border-top-left-radius", "border-top-right-radius",
      "border-bottom-left-radius", "border-bottom-right-radius",
      "font-size", "font-family", "font-weight", "line-height",
      "letter-spacing", "text-indent",
      "display", "position", "float", "clear", "box-sizing",
      "flex", "flex-basis", "flex-grow", "flex-shrink",
      "grid", "grid-template-columns", "grid-template-rows",
      "aspect-ratio", "transform", "object-fit", "object-position",
    ]);
    const darkRules =
      css.match(/[^{}]*\[data-color-scheme="dark"\][^{]*\{[^}]*\}/g) || [];
    expect(darkRules.length).toBeGreaterThan(0);
    for (const rule of darkRules) {
      const body = rule.slice(rule.indexOf("{") + 1, -1);
      const props = [...body.matchAll(/([a-zA-Z-]+)\s*:/g)]
        .map((m) => m[1].toLowerCase())
        .filter((prop) => !prop.startsWith("--"));
      for (const prop of props) {
        expect(
          GEOMETRY.has(prop),
          `propriedade de geometria "${prop}" em bloco escuro: ${rule.slice(0, 90)}`,
        ).toBe(false);
      }
    }
  });

  it("P6.2 R26: transição de cores ~200 ms só durante data-theme-transition, escopo na raiz", () => {
    const scoped = css.match(
      /\.delpi-ui-form-root\[data-theme-transition\]\s*,\s*\.delpi-ui-form-root\[data-theme-transition\]\s+:where\(\*\)\s*\{([^}]*)\}/,
    );
    expect(scoped, "regra de transição no atributo").toBeTruthy();
    const decl = normalize(scoped![1]);
    for (const prop of [
      "background-color",
      "border-color",
      "box-shadow",
      "color",
      "fill",
      "stroke",
    ]) {
      expect(decl).toContain(`${prop} 0.2s ease`);
    }
    expect(decl).not.toContain("!important");
    // Barra de progresso não perde a animação de largura durante a troca.
    const fill = css.match(
      /\.delpi-ui-form-root\[data-theme-transition\]\s+\.delpi-ui-form-progress__fill\s*\{([^}]*)\}/,
    );
    expect(fill, "transição do fill no atributo").toBeTruthy();
    expect(normalize(fill![1])).toContain("width 0.2s ease");
    // Movimento reduzido: troca imediata.
    const reduce = css.match(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*?)\n\}/,
    );
    expect(reduce, "bloco prefers-reduced-motion").toBeTruthy();
    expect(reduce![1]).toContain("transition: none");
  });

  it("P6.2 R26: nenhuma transição permanente fora do atributo (exceto a largura da barra)", () => {
    const rules = css.match(/([^{}@]+)\{([^{}]*transition[^{}]*)\}/g) || [];
    for (const rule of rules) {
      const selector = rule.slice(0, rule.indexOf("{")).trim();
      const body = rule.slice(rule.indexOf("{"));
      if (selector.includes("data-theme-transition")) continue;
      // Única transição permanente permitida: largura da barra de progresso.
      expect(
        selector,
        `transição permanente fora do atributo: ${selector}`,
      ).toBe(".delpi-ui-form-progress__fill");
      expect(body).not.toMatch(
        /(background-color|border-color|color|fill|stroke)\s/,
      );
    }
  });
});
