import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const cssPath = join(dirname(fileURLToPath(import.meta.url)), "dashboard-filters.css");
const css = readFileSync(cssPath, "utf8");

describe("dashboard-filters.css — filter-box em formulários", () => {
  it("garante width 100% em input/select/textarea fora de FiltersRow", () => {
    // Regressão: campos TextField/TextAreaField com dual-class delpi-ui-filter-box
    // encolhiam no FormGrid (width só existia sob .delpi-ui-filters-row).
    expect(css).toMatch(
      /\.delpi-ui-filter-box input:not\(\[type="checkbox"\]\):not\(\[type="radio"\]\),\s*\n\.delpi-ui-filter-box select,\s*\n\.delpi-ui-filter-box textarea \{\s*\n\s*width:\s*100%;/,
    );
  });
});
