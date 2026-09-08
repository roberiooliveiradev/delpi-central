import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(__dirname, "action-controls.css"), "utf8");

describe("action-controls FormActions spacing", () => {
  it("mantém margem entre ActionButtons dentro de FormActions", () => {
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*>\s*\.delpi-ui-action-btn\s*\+\s*\.delpi-ui-action-btn[\s\S]*?margin-inline-start:\s*16px/,
    );
    expect(css).not.toMatch(
      /\.delpi-ui-form-actions\s*>\s*\.delpi-ui-action-btn\s*\+\s*\.delpi-ui-action-btn[\s\S]*?margin-inline-start:\s*0\s*;/,
    );
  });
});
