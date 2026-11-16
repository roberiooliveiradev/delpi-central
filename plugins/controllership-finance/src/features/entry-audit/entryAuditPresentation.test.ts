import { describe, expect, it } from "vitest";

import {
  alignEntryAuditDailySeries,
  auditStatusBadgeVariant,
  conformityRatio,
  entryAuditDailyPointAriaLabel,
  entryAuditPreviousPeriodLabel,
  entryAuditPreviousPeriodRange,
  entryAuditTabResource,
  formatAnalysisScope,
  formatBranchLabel,
  formatBranches,
  formatDifference,
  abbreviateAccessKey,
  formatDocumentType,
  formatDocumentTypes,
  formatEntryAuditChartDay,
  formatMoneyBRL,
  formatMoneyBRLForKpi,
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
    expect(formatTheme("header")).toBe("Cabeçalho da nota");
    expect(formatTheme("item")).toBe("Itens da nota");
    expect(formatDocumentType("nfe")).toBe("NF-e");
    expect(formatDocumentTypes(["cte", "nfe"])).toBe("NF-e e CT-e");
    expect(abbreviateAccessKey("12345678901234567890123456789012345678901234")).toEqual({
      short: "123456…1234",
      full: "12345678901234567890123456789012345678901234",
    });
    expect(abbreviateAccessKey("2024-01-15T10:30:00")).toBeNull();
    expect(
      formatBranchLabel("01", [{ code: "01", name: "Matriz", state: "SC" }]),
    ).toBe("Filial 01 · SC");
    expect(formatBranchLabel("02")).toBe("Filial 02");
    expect(formatBranches(["01", "02"])).toBe("Filiais 01 e 02");
    expect(formatBranches(["01", "02", "03"])).toBe("Filiais 01, 02, 03");
    const opts = [
      { code: "01", state: "SC" },
      { code: "02", state: "ES" },
    ];
    expect(formatAnalysisScope(["01", "02"], ["nfe", "cte"], opts)).toBe(
      "Filiais 01 (SC) e 02 (ES) · NF-e e CT-e",
    );
    // BFF persiste sorted(set) → ["cte","nfe"]; escopo deve seguir ordem canônica.
    expect(formatAnalysisScope(["01", "02"], ["cte", "nfe"], opts)).toBe(
      "Filiais 01 (SC) e 02 (ES) · NF-e e CT-e",
    );
    expect(formatAnalysisScope(["01"], ["cte"], opts)).toBe("Filial 01 (SC) · CT-e");
  });

  it("formata dinheiro e diferença (código → —)", () => {
    expect(formatMoneyBRL(170)).toMatch(/R\$\s*170,00/);
    expect(formatDifference(170)).toMatch(/R\$\s*170,00/);
    expect(formatDifference("-29.92")).toMatch(/R\$/);
    expect(formatDifference(1, "CST")).toBe("—");
    expect(formatDifference(1, "cfop")).toBe("—");
    expect(formatDifference(null)).toBe("—");
    const compact = formatMoneyBRLForKpi(1_060_126.08);
    expect(compact.display).toBe("R$ 1,06 mi");
    expect(compact.title).toMatch(/R\$\s*1\.060\.126,08/);
    const small = formatMoneyBRLForKpi(170);
    expect(small.display).toMatch(/R\$\s*170,00/);
    expect(small.title).toBe(small.display);
  });

  it("mapeia tons de severidade e status", () => {
    expect(severityBadgeVariant("Alta")).toBe("danger");
    expect(severityBadgeVariant("Média")).toBe("warning");
    expect(severityBadgeVariant("Baixa")).toBe("neutral");
    expect(severityBadgeVariant("Info")).toBe("info");
    expect(auditStatusBadgeVariant("done")).toBe("success");
    expect(auditStatusBadgeVariant("failed")).toBe("danger");
  });

  it("alinha evolução diária por índice do dia (não pela data ISO)", () => {
    const points = alignEntryAuditDailySeries(
      [
        { name: "2026-11-01", count: 5 },
        { name: "2026-11-02", count: 12 },
      ],
      [
        { name: "2026-10-17", count: 8 },
        { name: "2026-10-31", count: 3 },
      ],
    );
    expect(points).toHaveLength(2);
    expect(points[0]?.name).toBe("01/11");
    expect(points[0]?.day).toBe("2026-11-01");
    expect(points[0]?.current).toBe(5);
    expect(points[0]?.previous).toBe(8);
    expect(points[0]?.previousDay).toBe("2026-10-17");
    expect(points[1]?.previous).toBe(3);
    expect(points[1]?.previousDay).toBe("2026-10-31");
    expect(formatEntryAuditChartDay("2026-11-05")).toBe("05/11");

    const solo = alignEntryAuditDailySeries(
      [{ name: "2026-11-01", count: 1 }],
      [],
    );
    expect(solo[0]?.previous).toBeUndefined();

    const aria = entryAuditDailyPointAriaLabel(points[1]!, true);
    expect(aria).toContain("12");
    expect(aria).toContain("31/10");
    expect(aria).toContain("3");
  });

  it("preenche todos os dias do período com zero (AC-GRA-3)", () => {
    const points = alignEntryAuditDailySeries(
      [{ name: "2026-11-09", count: 4 }],
      [],
      { dateFrom: "2026-11-07", dateTo: "2026-11-10" },
    );
    expect(points.map((p) => p.day)).toEqual([
      "2026-11-07",
      "2026-11-08",
      "2026-11-09",
      "2026-11-10",
    ]);
    expect(points.map((p) => p.current)).toEqual([0, 0, 4, 0]);
  });

  it("alinha anterior pelo índice do dia no período espelho (OC-1)", () => {
    // Atual 07–10/11; anterior espelho = 03–06/11. Dado só em 05/11 (= dia 3).
    const points = alignEntryAuditDailySeries(
      [{ name: "2026-11-09", count: 4 }],
      [{ name: "2026-11-05", count: 7 }],
      { dateFrom: "2026-11-07", dateTo: "2026-11-10" },
    );
    expect(points[0]?.day).toBe("2026-11-07");
    expect(points[0]?.previous).toBe(0);
    expect(points[2]?.day).toBe("2026-11-09");
    expect(points[2]?.previous).toBe(7);
    expect(points[2]?.previousDay).toBe("2026-11-05");
  });

  it("calcula rótulo do período anterior com o mesmo número de dias", () => {
    expect(entryAuditPreviousPeriodRange("2026-11-01", "2026-11-15")).toEqual([
      "2026-10-17",
      "2026-10-31",
    ]);
    expect(entryAuditPreviousPeriodLabel("2026-11-01", "2026-11-15")).toContain(
      "17",
    );
    expect(entryAuditPreviousPeriodLabel("2026-11-01", "2026-11-15")).toContain(
      "31",
    );
  });

  it("formata nota/série e razão de conformidade", () => {
    expect(formatPeriodLabel("2026-11-12", "2026-11-12")).toContain("2026");
    expect(formatNoteSeries("123", "1")).toBe("123/1");
    expect(conformityRatio(8, 2)).toBe(80);
    expect(conformityRatio(0, 0)).toBe(100);
  });
});
