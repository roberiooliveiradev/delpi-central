import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(join(__dirname, "action-controls.css"), "utf8");

describe("action-controls FormActions spacing", () => {
  it("define gap canônico de 24px no FormActions", () => {
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*\{[^}]*gap:\s*var\(--delpi-ui-form-actions-gap,\s*24px\)/,
    );
    expect(css).toMatch(
      /\.delpi-ui-form-actions\s*>\s*\.delpi-ui-action-btn\s*\+\s*\.delpi-ui-action-btn[\s\S]*?margin-inline-start:\s*0/,
    );
  });
});
