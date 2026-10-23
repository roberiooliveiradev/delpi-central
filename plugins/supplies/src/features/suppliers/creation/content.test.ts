import { describe, expect, it } from "vitest";

import {
  formatRetrievedAt,
  PORTAL_TIME_ZONE,
  providerDisplayName,
} from "./content";

describe("formatRetrievedAt — fuso de apresentação (S9.B / AC-08)", () => {
  it("projeta instante UTC em America/Sao_Paulo (UTC-3, sem DST)", () => {
    expect(PORTAL_TIME_ZONE).toBe("America/Sao_Paulo");
    expect(formatRetrievedAt("2026-10-23T13:47:00Z")).toBe(
      "23/10/2026 às 10:47 (horário de Brasília)",
    );
  });

  it("timestamp com offset explícito é respeitado como instante", () => {
    expect(formatRetrievedAt("2026-10-23T10:47:00-03:00")).toBe(
      "23/10/2026 às 10:47 (horário de Brasília)",
    );
    // mesmo instante, outra escrita → mesma exibição
    expect(formatRetrievedAt("2026-10-23T16:47:00+03:00")).toBe(
      "23/10/2026 às 10:47 (horário de Brasília)",
    );
  });

  it("a conversão pode cruzar a meia-noite e mudar a data", () => {
    expect(formatRetrievedAt("2026-10-23T01:30:00Z")).toBe(
      "22/10/2026 às 22:30 (horário de Brasília)",
    );
    expect(formatRetrievedAt("2026-01-01T02:59:00Z")).toBe(
      "31/12/2025 às 23:59 (horário de Brasília)",
    );
  });

  it("a exibição é fixa no fuso do Portal — não do relógio local", () => {
    // O mesmo instante sempre renderiza a mesma hora de Brasília,
    // independente do TZ do processo (o timeZone é passado explicitamente).
    const iso = "2026-10-23T13:47:00Z";
    const first = formatRetrievedAt(iso);
    const second = formatRetrievedAt(iso);
    expect(first).toBe(second);
    expect(first).toContain("10:47");
  });

  it("timestamp inválido devolve o valor original sem quebrar", () => {
    expect(formatRetrievedAt("not-a-date")).toBe("not-a-date");
    expect(formatRetrievedAt("")).toBe("");
  });
});

describe("providerDisplayName — fonte humanizada (S9.C / AC-09)", () => {
  it("BrasilAPI recebe nome amigável sem reivindicar base oficial", () => {
    const label = providerDisplayName("brasilapi-cnpj-v1");
    expect(label).toBe("BrasilAPI — dados públicos de terceiros");
    expect(label).not.toMatch(/Receita Federal|oficial|homologa/i);
  });

  it("provedor desconhecido usa fallback honesto (o próprio id)", () => {
    expect(providerDisplayName("outro-provedor-x")).toBe("outro-provedor-x");
    expect(providerDisplayName("")).toBe("");
  });
});
