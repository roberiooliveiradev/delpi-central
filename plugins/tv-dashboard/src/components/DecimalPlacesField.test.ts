import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "DecimalPlacesField.tsx"),
  "utf8",
);

describe("DecimalPlacesField", () => {
  it("usa NumberStepperControl como o tamanho de fonte (− / valor / +)", () => {
    expect(source).toContain("NumberStepperControl");
    expect(source).toContain("onStepDown");
    expect(source).toContain("onStepUp");
    expect(source).not.toMatch(/<\s*ComboboxNumberControl\b/);
  });
});
