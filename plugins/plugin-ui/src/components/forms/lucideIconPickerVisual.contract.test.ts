import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("lucide icon picker visual contract", () => {
  const css = readFileSync(resolve(__dirname, "../../styles/lucide-icon-picker.css"), "utf8");
  const stylesEntry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");

  it("está importado no styles.css do kit", () => {
    expect(stylesEntry).toContain('import "./styles/lucide-icon-picker.css"');
  });

  it("mantém elevação sem blur (popover opaco)", () => {
    expect(css).toMatch(/border-radius:\s*20px/);
    expect(css).not.toMatch(/\.delpi-ui-lucide-icon-picker-popover\s*\{[^}]*backdrop-filter/s);
    expect(css).toContain(".delpi-ui-lucide-icon-picker__selected");
    expect(css).toMatch(/min-height:\s*40px/);
  });
});
