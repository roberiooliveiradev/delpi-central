import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("popover surface visual contract", () => {
  const css = readFileSync(resolve(__dirname, "../../styles/popover-surface.css"), "utf8");
  const stylesEntry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");

  it("está no styles.css e define tokens únicos", () => {
    expect(stylesEntry).toContain('import "./styles/popover-surface.css"');
    expect(css).toContain("--delpi-ui-popover-radius: 12px");
    expect(css).toContain("--delpi-ui-popover-shadow");
    expect(css).toContain("--delpi-ui-popover-bg");
    expect(css).toContain(".delpi-ui-popover-surface");
    expect(css).toContain(".delpi-ui-shape-menu__panel");
    expect(css).toContain(".delpi-ui-ribbon-group__popover");
    expect(css).toContain(".delpi-ui-lucide-icon-picker-popover");
    expect(css).toContain("backdrop-filter: none");
  });
});
