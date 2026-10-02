import { describe, expect, it } from "vitest";
import {
  formatCycleSeconds, formatPerformancePercent, formatPiecesPerHour,
  isLowPerformance, performancePaceLabel, performanceQualityHint, standardTimeSourceLabel,
} from "./performance";

describe("performance formatters", () => {
  it("formats percent with pt-BR and never clamps above 100", () => {
    expect(formatPerformancePercent(85.714)).toBe("85,7%");
    expect(formatPerformancePercent(111.11)).toBe("111,1%");
    expect(formatPerformancePercent(100)).toBe("100,0%");
    expect(formatPerformancePercent(0)).toBe("0,0%");
  });
  it("renders null/undefined as unavailable, never as 0%", () => {
    expect(formatPerformancePercent(null)).toBe("—");
    expect(formatPerformancePercent(undefined)).toBe("—");
    expect(formatPerformancePercent(null)).not.toBe("0,0%");
  });
  it("formats cycle seconds and pieces per hour", () => {
    expect(formatCycleSeconds(1.8)).toBe("1,80 s");
    expect(formatCycleSeconds(null)).toBe("—");
    expect(formatPiecesPerHour(1714.285714)).toBe("1.714 pç/h");
    expect(formatPiecesPerHour(2000)).toBe("2.000 pç/h");
    expect(formatPiecesPerHour(null)).toBe("—");
  });
  it("labels pace factually against the 100% standard", () => {
    expect(performancePaceLabel(111.11)).toBe("Acima do ritmo padrão");
    expect(performancePaceLabel(100)).toBe("No ritmo padrão");
    expect(performancePaceLabel(85.7)).toBe("Abaixo do ritmo padrão");
    expect(performancePaceLabel(null)).toBeNull();
  });
  it("marks only values below 90% as low performance", () => {
    expect(isLowPerformance(89.9)).toBe(true);
    expect(isLowPerformance(85.71)).toBe(true);
    expect(isLowPerformance(90)).toBe(false);
    expect(isLowPerformance(111.11)).toBe(false);
    expect(isLowPerformance(null)).toBe(false);
  });
});

describe("performance data quality", () => {
  const codes = [
    "standard_time_unavailable", "piece_conversion_unavailable", "upstream_unavailable",
    "insufficient_count_data", "insufficient_producing_time", "invalid_standard_time_snapshot",
  ];
  it.each(codes)("maps %s to friendly copy, never the raw code", (code) => {
    const hint = performanceQualityHint(code);
    expect(hint).not.toBeNull();
    expect(hint!.short).not.toContain("_");
    expect(hint!.detail).not.toContain("_");
    expect(hint!.detail).not.toContain(code);
  });
  it("keeps the card quiet when data is complete", () => {
    expect(performanceQualityHint("complete")).toBeNull();
    expect(performanceQualityHint(null)).toBeNull();
    expect(performanceQualityHint(undefined)).toBeNull();
  });
  it("distinguishes waiting-for-production from hard unavailability", () => {
    expect(performanceQualityHint("insufficient_count_data")!.short).toBe("Aguardando produção");
    expect(performanceQualityHint("insufficient_producing_time")!.short).toBe("Aguardando produção");
    expect(performanceQualityHint("standard_time_unavailable")!.short).toBe("Indisponível");
  });
  it("falls back gracefully for unknown codes", () => {
    const hint = performanceQualityHint("future_code");
    expect(hint).not.toBeNull();
    expect(hint!.detail).not.toContain("future_code");
  });
});

describe("standard time source", () => {
  it("translates TOTVS origins without exposing table codes", () => {
    expect(standardTimeSourceLabel("shy_tempad")).toBe("Padrão da ordem de produção");
    expect(standardTimeSourceLabel("shy_tempom_quant")).toBe("Padrão calculado da ordem de produção");
    expect(standardTimeSourceLabel("sg2_tempad")).toBe("Padrão do roteiro");
    expect(standardTimeSourceLabel(null)).toBe("Não disponível");
    for (const value of ["shy_tempad", "sg2_tempad"]) {
      expect(standardTimeSourceLabel(value)).not.toMatch(/shy|sg2/i);
    }
  });
});
