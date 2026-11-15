import { describe, expect, it } from "vitest";

import {
  conformityRatio,
  entryAuditClaraSuggestions,
  entryAuditOccurrenceClaraPrompt,
  formatPeriodLabel,
  parseEntryAuditTab,
  severityFromUrl,
  severityToUrl,
} from "./entryAuditPresentation";

describe("entryAuditPresentation", () => {
  it("mantém o mapa de severidade estável na URL", () => {
    expect(severityFromUrl("high")).toBe("Alta");
    expect(severityToUrl("Depende da TES")).toBe("depends_on_tes");
    expect(severityFromUrl("custom")).toBe("custom");
  });

  it("rejeita abas desconhecidas", () => {
    expect(parseEntryAuditTab("cte")).toBe("cte");
    expect(parseEntryAuditTab("unknown")).toBe("occurrences");
  });

  it("monta sugestões e prompt da CLARA com o período", () => {
    expect(formatPeriodLabel("2026-11-12", "2026-11-12")).toContain("2026");
    expect(entryAuditClaraSuggestions("2026-11-12", "2026-11-12")[0]).toMatch(
      /auditoria de entradas/,
    );
    expect(
      entryAuditOccurrenceClaraPrompt("01|key", "2026-11-12", "2026-11-12"),
    ).toContain("01|key");
    expect(conformityRatio(8, 2)).toBe(80);
    expect(conformityRatio(0, 0)).toBe(100);
  });
});
