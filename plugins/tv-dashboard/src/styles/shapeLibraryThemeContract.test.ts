import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Flyout Formas: nav e painel devem seguir tokens do popover (claro/escuro).
 * Regressão: `--td-surface-2` / `#f8fafc` deixava a lateral clara com texto branco no dark.
 */
describe("shape library theme contract", () => {
  it("nav do flyout usa wash relativo ao tema, sem fallback claro fixo", () => {
    const css = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../index.css"), "utf8");
    const navBlock = css.match(/\.td-shape-library__nav\{[\s\S]*?\n\}/)?.[0] ?? "";
    expect(navBlock).toContain("--delpi-ui-popover-bg");
    expect(navBlock).toContain("--delpi-ui-text");
    expect(navBlock).not.toMatch(/#f8fafc/);
    expect(navBlock).not.toMatch(/--td-surface-2/);
    expect(navBlock).not.toMatch(/--delpi-ui-surface-2/);

    const flyoutBlock = css.match(/\.td-shape-library--flyout\{[\s\S]*?\n\}/)?.[0] ?? "";
    expect(flyoutBlock).toContain("--delpi-ui-popover-bg");
    expect(flyoutBlock).toContain("color: var(--delpi-ui-text");
  });
});
