/**
 * AC-CLARA-4 — análise e detalhe não renderizam «CLARA» no Portal.
 * A CLARA permanece como MCP externo + ClaraConsentPage.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const DIR = __dirname;

describe("U14 F5 — CLARA fora do Portal (AC-CLARA-4)", () => {
  it("EntryAuditAnalysisPage não menciona CLARA", () => {
    const source = readFileSync(
      join(DIR, "EntryAuditAnalysisPage.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/CLARA/i);
    expect(source).not.toMatch(/Pergunte à/i);
  });

  it("EntryAuditOccurrencePage não menciona CLARA nem clara_suggestion", () => {
    const source = readFileSync(
      join(DIR, "EntryAuditOccurrencePage.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/CLARA/i);
    expect(source).not.toMatch(/clara_suggestion/);
    expect(source).not.toMatch(/Copiar pergunta/i);
  });

  it("tipo MFE de ocorrência não expõe clara_suggestion", () => {
    const source = readFileSync(
      join(DIR, "../../api/entryAuditApi.ts"),
      "utf8",
    );
    expect(source).not.toMatch(/clara_suggestion/);
  });
});
