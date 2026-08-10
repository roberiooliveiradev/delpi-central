import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Divisor da ribbon: uma só fonte (kit border-left entre grupos).
 * MFE dual-class não pode somar border-right — gerava linha dupla.
 */
describe("ribbon group divider contract", () => {
  const kit = readFileSync(resolve(here, "ribbon-overflow.css"), "utf8");
  const mfe = readFileSync(
    resolve(here, "../../../tv-dashboard/src/index.css"),
    "utf8",
  );

  it("kit define border-left entre grupos adjacentes", () => {
    expect(kit).toMatch(
      /\.delpi-ui-ribbon-group\s*\+\s*\.delpi-ui-ribbon-group\s*\{[^}]*border-left:\s*1px/s,
    );
  });

  it("kit permite encolher grupos e wide ocupa folga", () => {
    const group = kit.match(/\.delpi-ui-ribbon-group\s*\{[^}]+\}/s)?.[0];
    expect(group).toMatch(/flex:\s*0\s+1\s+auto/);
    const wide = kit.match(/\.delpi-ui-ribbon-group--wide\s*\{[^}]+\}/s)?.[0];
    expect(wide).toMatch(/flex:\s*1\s+1\s+auto/);
  });

  it("MFE não pinta border-right 1px nos grupos da ribbon (evita linha dupla)", () => {
    const base = mfe.match(
      /\.dashboard-tv-dashboard \.td-deck-ribbon__group\s*\{[^}]+\}/s,
    )?.[0];
    expect(base).toBeTruthy();
    expect(base).not.toMatch(/border-right:\s*1px/);
    expect(base).toMatch(/border-right:\s*none/);
  });

  it("corpo do grupo centraliza itens na horizontal", () => {
    const body = kit.match(/\.delpi-ui-ribbon-group__body\s*\{[^}]+\}/s)?.[0];
    expect(body).toBeTruthy();
    expect(body).toMatch(/justify-content:\s*center/);
    expect(body).toMatch(/align-items:\s*center/);
    expect(body).toMatch(/width:\s*100%/);
  });
});
