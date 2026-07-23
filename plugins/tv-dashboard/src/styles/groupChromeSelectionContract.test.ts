import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const base = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(base, "../index.css"), "utf8");

describe("group chrome selection contract", () => {
  it("não cobre o grupo com pointer-events:auto no container de handles", () => {
    /*
     * Regressão: `.td-composer__group-chrome .td-composer__block-handles { pointer-events: auto }`
     * engolia o 2º clique nos membros e impedia isolar subitens.
     */
    const override = css.match(
      /\.td-composer__group-chrome\s+\.td-composer__block-handles\s*\{[^}]*\}/,
    );
    expect(override?.[0] ?? "").toContain("pointer-events: none");
    expect(override?.[0] ?? "").not.toMatch(/pointer-events:\s*auto/);
  });

  it("tem contorno pai para filhos isolados", () => {
    expect(css).toContain("td-composer__group-chrome--parent-hint");
  });
});
