import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "user-manual.css"), "utf8");

describe("user-manual.css — chrome compartilhado", () => {
  it("define layout, TOC e tabela canônicos sem prefixo de MFE", () => {
    expect(css).toMatch(/\.delpi-ui-user-manual__layout\s*\{/);
    expect(css).toMatch(/\.delpi-ui-user-manual__toc\s*\{/);
    expect(css).toMatch(/\.delpi-ui-user-manual__table\s*\{/);
    expect(css).toMatch(/\.delpi-ui-user-manual__faq(?:,\s*\.delpi-ui-user-manual__glossary)?\s*\{/);
    expect(css).not.toMatch(/\.cm-user-manual\s*\{/);
    expect(css).not.toMatch(/\.sp-user-manual\s*\{/);
    expect(css).not.toMatch(/\.tm-user-manual\s*\{/);
  });
});
