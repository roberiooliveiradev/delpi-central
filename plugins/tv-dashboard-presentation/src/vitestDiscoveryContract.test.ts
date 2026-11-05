import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const packageRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("vitest and playwright discovery", () => {
  const vitestConfig = readFileSync(join(packageRoot, "vitest.config.ts"), "utf8");
  const playwrightConfig = readFileSync(join(packageRoot, "e2e/playwright.config.ts"), "utf8");

  it("vitest keeps the default excludes and drops only the playwright tree", () => {
    expect(vitestConfig).toMatch(/configDefaults\.exclude/);
    expect(vitestConfig).toMatch(/exclude:\s*\[\s*\.\.\.configDefaults\.exclude,\s*"e2e\/\*\*"\s*\]/);
    expect(vitestConfig).not.toMatch(/passWithNoTests/);
    expect(vitestConfig).not.toMatch(/\*\.spec\.ts/);
  });

  it("playwright remains the owner of e2e/specs", () => {
    expect(playwrightConfig).toMatch(/testDir:\s*"\.\/specs"/);
    for (const spec of ["presentation-capture.spec.ts", "kpi-status-capture.spec.ts"]) {
      const source = readFileSync(join(packageRoot, "e2e/specs", spec), "utf8");
      expect(source).toMatch(/from "@playwright\/test"/);
    }
  });

  it("a presentation unit test does not import playwright", () => {
    const source = readFileSync(join(packageRoot, "src/tvDataChartWidgets.percentage.test.tsx"), "utf8");
    expect(source).not.toMatch(/@playwright\/test/);
    expect(source).toMatch(/from "vitest"/);
  });
});
