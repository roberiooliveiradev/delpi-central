import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("lucide icon picker visual contract", () => {
  const css = readFileSync(resolve(__dirname, "../../styles/lucide-icon-picker.css"), "utf8");
  const popoverCss = readFileSync(resolve(__dirname, "../../styles/popover-surface.css"), "utf8");
  const stylesEntry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");

  it("está importado no styles.css do kit", () => {
    expect(stylesEntry).toContain('import "./styles/lucide-icon-picker.css"');
    expect(stylesEntry).toContain('import "./styles/popover-surface.css"');
  });

  it("usa chrome canônico de popover (sem blur) e mantém cards", () => {
    expect(popoverCss).toContain("--delpi-ui-popover-radius");
    expect(popoverCss).toContain("--delpi-ui-popover-shadow");
    expect(popoverCss).toContain("--delpi-ui-popover-bg");
    expect(popoverCss).toContain(".delpi-ui-lucide-icon-picker-popover");
    expect(popoverCss).not.toMatch(/backdrop-filter:\s*blur/);
    expect(css).toContain("background: transparent");
    expect(css).toContain("--delpi-ui-popover-bg");
    expect(css).toContain(".delpi-ui-lucide-icon-picker__selected");
    expect(css).toMatch(/min-height:\s*40px/);
    expect(css).not.toContain("delpi-ui-lucide-icon-picker__close");
  });
});
