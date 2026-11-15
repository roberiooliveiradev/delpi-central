import { describe, expect, it } from "vitest";

import {
  auditStatusBadgeVariant,
  conformityRatio,
  entryAuditClaraSuggestions,
  entryAuditOccurrenceClaraPrompt,
  entryAuditTabResource,
  formatBranchLabel,
  formatDifference,
  formatDocumentType,
  formatDocumentTypes,
  formatMoneyBRL,
  formatNoteSeries,
  formatPeriodLabel,
  formatTheme,
  parseEntryAuditTab,
  severityBadgeVariant,
  severityFromUrl,
  severityToUrl,
} from "./entryAuditPresentation";

describe("entryAuditPresentation", () => {
  it("mantém o mapa de severidade estável na URL", () => {
    expect(severityFromUrl("high")).toBe("Alta");
    expect(severityToUrl("Depende da TES")).toBe("depends_on_tes");
    expect(severityFromUrl("custom")).toBe("custom");
  });

  it("rejeita abas desconhecidas e mapeia posted_outside → documents", () => {
    expect(parseEntryAuditTab("cte")).toBe("cte");
    expect(parseEntryAuditTab("unknown")).toBe("occurrences");
    expect(parseEntryAuditTab("posted_outside")).toBe("posted_outside");
    expect(entryAuditTabResource("posted_outside")).toBe("documents");
    expect(entryAuditTabResource("unmatched")).toBe("unmatched");
  });

  it("traduz temas e tipos para vocabulário de negócio", () => {
    expect(formatTheme("cte")).toBe("CT-e");
    expect(formatTheme("header")).toBe("Cabeçalho");
    expect(formatDocumentType("nfe")).toBe("NF-e");
    expect(formatDocumentTypes(["cte", "nfe"])).toBe("CT-e, NF-e");
    expect(
      formatBranchLabel("01", [{ code: "01", name: "Matriz", state: "SC" }]),
    ).toBe("Filial 01 · SC");
    expect(formatBranchLabel("02")).toBe("Filial 02");
  });

  it("formata dinheiro e diferença (código → —)", () => {
    expect(formatMoneyBRL(170)).toMatch(/R\$\s*170,00/);
    expect(formatDifference(170)).toMatch(/R\$\s*170,00/);
    expect(formatDifference("-29.92")).toMatch(/R\$/);
    expect(formatDifference(1, "CST")).toBe("—");
    expect(formatDifference(1, "cfop")).toBe("—");
    expect(formatDifference(null)).toBe("—");
  });

  it("mapeia tons de severidade e status", () => {
    expect(severityBadgeVariant("Alta")).toBe("danger");
    expect(severityBadgeVariant("Média")).toBe("warning");
    expect(severityBadgeVariant("Baixa")).toBe("neutral");
    expect(severityBadgeVariant("Info")).toBe("info");
    expect(auditStatusBadgeVariant("done")).toBe("success");
    expect(auditStatusBadgeVariant("failed")).toBe("danger");
  });

  it("monta sugestões e prompt da CLARA", () => {
    expect(formatPeriodLabel("2026-11-12", "2026-11-12")).toContain("2026");
    expect(entryAuditClaraSuggestions("2026-11-12", "2026-11-12")).toEqual([
      "Explique as Altas",
      "O que fazer com as notas sem par?",
      "Compare com o período anterior",
    ]);
    expect(
      entryAuditOccurrenceClaraPrompt("01|key", "2026-11-12", "2026-11-12"),
    ).toContain("01|key");
    expect(formatNoteSeries("123", "1")).toBe("123/1");
    expect(conformityRatio(8, 2)).toBe(80);
    expect(conformityRatio(0, 0)).toBe(100);
  });
});
