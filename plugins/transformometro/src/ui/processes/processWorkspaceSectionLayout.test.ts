import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("tm-processo-workspace section layout", () => {
  it("seções inativas usam display:none (não absolute) para não inflar scroll de .content", () => {
    const css = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");

    expect(css).toMatch(
      /\.dashboard-transformometro\s+\.tm-processo-workspace-section\s*\{[^}]*display:\s*none/s,
    );
    expect(css).toMatch(
      /\.dashboard-transformometro\s+\.tm-processo-workspace-section--active\s*\{[^}]*display:\s*flex/s,
    );
    // Regressão: abspos + visibility:hidden fazia overflow fantasma no portal.
    expect(css).not.toMatch(
      /\.tm-processo-workspace-section\s*\{[^}]*position:\s*absolute/s,
    );
  });
});
