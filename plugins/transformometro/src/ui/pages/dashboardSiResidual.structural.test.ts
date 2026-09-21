import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const srcRoot = join(dirname(fileURLToPath(import.meta.url)), "../..");

function readSrc(relative: string): string {
  return readFileSync(join(srcRoot, relative), "utf8");
}

describe("Transforma+ SI residual", () => {
  it("não calcula IDD/meta no MFE e não importa internals", () => {
    const page = readSrc("ui/pages/DashboardPage.tsx");
    const presentation = readSrc("utils/dashboardGrossSavingsPresentation.ts");
    const api = readSrc("data/api/transformometroApi.ts");
    const combined = [page, presentation, api].join("\n");
    expect(combined).not.toMatch(/calculateIndicatorIddScore/);
    expect(combined).not.toMatch(/monthly_target\s*\/\s*days/);
    expect(combined).not.toMatch(/from ["']@delpi\/commercial/);
    expect(combined).not.toMatch(/\/apps\/api-delpi/);
    expect(combined).not.toMatch(/StrategicIndicatorsRepository/);
    expect(page).toMatch(/iddScoreLabel=\{grossSavingsPresentation\.iddScoreLabel\}/);
    expect(presentation).toMatch(/pickSiIddScoreLabel/);
  });
});
