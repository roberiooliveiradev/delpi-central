import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const page = readFileSync(join(dir, "EntryAuditAnalysisPage.tsx"), "utf8");

describe("EntryAuditAnalysisPage progressive load (U9 R1)", () => {
  it("não usa Promise.all de analysis+summary+breakdowns no mount", () => {
    expect(page).not.toMatch(
      /Promise\.all\(\[\s*getEntryAuditAnalysis[\s\S]*getEntryAuditSummary[\s\S]*getEntryAuditBreakdowns/,
    );
  });

  it("mostra KPIs com analysis+summary e atrasa breakdowns/rows", () => {
    expect(page).toMatch(/getEntryAuditAnalysis/);
    expect(page).toMatch(/getEntryAuditSummary/);
    expect(page).toMatch(/getEntryAuditBreakdowns/);
    expect(page).toMatch(/if \(!analysis \|\| !summary\)/);
    expect(page).toMatch(/if \(!summary\) return;/);
    expect(page).toMatch(/breakdowns \?/);
    expect(page).toMatch(/serverPagination=/);
    expect(page).toMatch(/tablePage/);
  });
});
