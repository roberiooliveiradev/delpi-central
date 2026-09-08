import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "top-bar.css"), "utf8");

describe("top-bar.css — TopBar chrome compacto", () => {
  it("define pill canônico delpi-ui-topbar-search com kbd e hide mobile", () => {
    expect(css).toMatch(/\.delpi-ui-topbar-search\s*\{/);
    expect(css).toMatch(/\.delpi-ui-topbar-search__kbd\s*\{/);
    expect(css).toMatch(
      /@media \(max-width:\s*720px\)[\s\S]*\.delpi-ui-topbar-search__label[\s\S]*\.delpi-ui-topbar-search__kbd/,
    );
    // Negative: não depende de prefixo de MFE no CSS do kit.
    expect(css).not.toMatch(/\.cm-topbar-search\s*\{/);
    expect(css).not.toMatch(/\.sp-shell-secondary__search/);
  });

  it("expõe delpi-ui-topbar-collapse-label para Favoritos/nome/avatar dual-class", () => {
    expect(css).toMatch(/\.delpi-ui-topbar-collapse-label\s*\{/);
    expect(css).toMatch(
      /@media \(max-width:\s*720px\)[\s\S]*\.delpi-ui-topbar-collapse-label[\s\S]*clip:\s*rect\(0,\s*0,\s*0,\s*0\)/,
    );
    expect(css).not.toMatch(/\.cm-shell-user__name\s*\{/);
    expect(css).not.toMatch(/\.cm-shell-favorites__trigger-label\s*\{/);
  });
});
