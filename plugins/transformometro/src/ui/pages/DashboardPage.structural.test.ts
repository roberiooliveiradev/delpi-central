import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "DashboardPage.tsx"), "utf8");

describe("DashboardPage shared chrome", () => {
  it("usa contexto canônico e IDD/meta do SI sem fórmula local", () => {
    expect(source).toMatch(/buildDashboardKpiContextLabel/);
    expect(source).toMatch(/buildGrossSavingsKpiPresentation/);
    expect(source).toMatch(/pickSiIddScoreLabel|iddScoreLabel=\{grossSavingsPresentation/);
    expect(source).toMatch(/DepartmentScoreBadge/);
    expect(source).toMatch(/fetchDashboardStrategicIndicators/);
    expect(source).not.toMatch(/calculateIndicatorIddScore/);
    expect(source).not.toMatch(/\/apps\/api-delpi/);
    expect(source).not.toMatch(/sum\(/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
  });
});
