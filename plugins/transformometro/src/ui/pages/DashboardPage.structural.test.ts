import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "DashboardPage.tsx"), "utf8");

describe("DashboardPage shared chrome", () => {
  it("usa contexto canônico nos KpiCards e não calcula IDD no React", () => {
    expect(source).toMatch(/buildDashboardKpiContextLabel/);
    expect(source).toMatch(/contextLabel=\{kpiContext\}/);
    expect(source).not.toMatch(/iddScoreLabel/);
    expect(source).not.toMatch(/goalLabel=/);
    expect(source).not.toMatch(/sum\(/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
  });
});
