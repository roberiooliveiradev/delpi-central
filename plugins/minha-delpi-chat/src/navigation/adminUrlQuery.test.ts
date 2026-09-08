import { describe, expect, it } from "vitest";

import {
  parseAuditFiltersFromSearch,
  parseKnowledgeFiltersFromSearch,
  parseMetricsHoursFromSearch,
  serializeAuditFiltersToQuery,
  serializeKnowledgeFiltersToQuery,
  serializeMetricsHoursToQuery,
} from "./adminUrlQuery";

describe("adminUrlQuery", () => {
  it("parseia e serializa filtros de auditoria", () => {
    const parsed = parseAuditFiltersFromSearch(
      "?q=login&traceId=abc-1&context=chat&action=update",
    );
    expect(parsed).toEqual({
      search: "login",
      context: "chat",
      action: "update",
      userId: "",
      traceId: "abc-1",
      dateFrom: "",
      dateTo: "",
    });
    expect(serializeAuditFiltersToQuery(parsed)).toEqual({
      q: "login",
      context: "chat",
      action: "update",
      userId: null,
      traceId: "abc-1",
      dateFrom: null,
      dateTo: null,
    });
  });

  it("parseia knowledge com status e ignora status inválido", () => {
    expect(parseKnowledgeFiltersFromSearch("?q=norma&status=active&category=ops")).toEqual({
      search: "norma",
      status: "active",
      category: "ops",
      namespace: "",
      domain: "",
      tag: "",
      sourceType: "",
    });
    expect(parseKnowledgeFiltersFromSearch("?status=weird").status).toBe("all");
    expect(
      serializeKnowledgeFiltersToQuery({
        search: "",
        status: "all",
        category: "ops",
        namespace: "",
        domain: "",
        tag: "",
        sourceType: "",
      }),
    ).toEqual({
      q: null,
      status: null,
      category: "ops",
      namespace: null,
      domain: null,
      tag: null,
      sourceType: null,
    });
  });

  it("aceita apenas hours canônicos de métricas", () => {
    expect(parseMetricsHoursFromSearch("?hours=168")).toBe(168);
    expect(parseMetricsHoursFromSearch("?hours=999")).toBe(24);
    expect(serializeMetricsHoursToQuery(24)).toEqual({ hours: null });
    expect(serializeMetricsHoursToQuery(720)).toEqual({ hours: "720" });
  });
});
