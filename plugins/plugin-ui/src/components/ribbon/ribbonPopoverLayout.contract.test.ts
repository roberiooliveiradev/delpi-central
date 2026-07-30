import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("ribbon popover layout contract", () => {
  const overflowCss = readFileSync(
    resolve(__dirname, "../../styles/ribbon-overflow.css"),
    "utf8",
  );
  const tileCss = readFileSync(resolve(__dirname, "../../styles/ribbon-tile.css"), "utf8");

  it("quebra tiles no popover e evita vazamento horizontal", () => {
    expect(overflowCss).toContain(".delpi-ui-ribbon-group__popover .delpi-ui-ribbon-tiles");
    expect(overflowCss).toMatch(/\.delpi-ui-ribbon-group__popover \.delpi-ui-ribbon-tiles\s*\{[^}]*flex-wrap:\s*wrap/s);
    expect(overflowCss).toMatch(/\.delpi-ui-ribbon-group__popover\s*\{[^}]*overflow:\s*hidden/s);
    expect(overflowCss).toMatch(/\.delpi-ui-ribbon-group__popover-body\s*\{[^}]*flex-direction:\s*column/s);
  });

  it("permite até 2 linhas no rótulo do tile (sem ellipsis de uma linha)", () => {
    expect(tileCss).toContain("-webkit-line-clamp: 2");
    expect(tileCss).not.toMatch(
      /\.delpi-ui-ribbon-tile__label\s*\{[^}]*text-overflow:\s*ellipsis/s,
    );
  });
});
