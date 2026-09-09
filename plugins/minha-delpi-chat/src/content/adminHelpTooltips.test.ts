import { describe, expect, it } from "vitest";

import { ADMIN_HELP, getAdminHelp, listAdminHelpKeys } from "./adminHelpTooltips";

function collectStrings(value: unknown, acc: string[] = []): string[] {
  if (typeof value === "string") {
    acc.push(value);
    return acc;
  }
  if (value && typeof value === "object") {
    for (const nested of Object.values(value as Record<string, unknown>)) {
      collectStrings(nested, acc);
    }
  }
  return acc;
}

describe("adminHelpTooltips", () => {
  it("cobre as seções principais do admin", () => {
    expect(ADMIN_HELP.pages.overview.length).toBeGreaterThan(20);
    expect(ADMIN_HELP.pages.overview).toMatch(/fila de atenção/i);
    expect(ADMIN_HELP.pages.metrics).toMatch(/drill-down|atenção|URL|hours/i);
    expect(ADMIN_HELP.pages.audit).toMatch(/URL|filtro/i);
    expect(ADMIN_HELP.pages.documents).toMatch(/URL|filtro/i);
    expect(ADMIN_HELP.pages.specialization).toMatch(/Studio/i);
    expect(ADMIN_HELP.pages.finetuning).toMatch(/export/i);
    expect(ADMIN_HELP.pages.response.length).toBeGreaterThan(20);
    expect(ADMIN_HELP.pages.vision.length).toBeGreaterThan(20);
    expect(ADMIN_HELP.pages.learningPipeline.length).toBeGreaterThan(20);
    expect(ADMIN_HELP.studio.name.length).toBeGreaterThan(10);
    expect(ADMIN_HELP.kpis.qualityUnified.csat.length).toBeGreaterThan(10);
  });

  it("resolve chaves dotted", () => {
    expect(getAdminHelp("pages.documents")).toBe(ADMIN_HELP.pages.documents);
    expect(getAdminHelp("fields.documents.search")).toBe(ADMIN_HELP.fields.documents.search);
    expect(getAdminHelp("missing.key")).toBe("");
    expect(listAdminHelpKeys().length).toBeGreaterThan(40);
  });

  it("não vaza paths técnicos de API", () => {
    const texts = collectStrings(ADMIN_HELP);
    for (const text of texts) {
      expect(text).not.toMatch(/\/admin\//);
      expect(text).not.toMatch(/operationId/i);
    }
  });

  it("descreve OpenAPI-first sem pathMarkers", () => {
    expect(ADMIN_HELP.pages.tools).toMatch(/OpenAPI/i);
    expect(ADMIN_HELP.pages.tools).toMatch(/roteamento|schema|contrato/i);
    expect(ADMIN_HELP.pages.tools).toMatch(/registry|endpoint/i);
    expect(ADMIN_HELP.pages.intelligence).toMatch(/OpenAPI-first/i);
  });
});
