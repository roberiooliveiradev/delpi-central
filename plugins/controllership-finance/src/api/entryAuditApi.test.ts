import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getEntryAuditSummary,
  listEntryAuditRows,
} from "./entryAuditApi";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("entryAuditApi", () => {
  it("mapeia o envelope público e branches indisponíveis", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            kpis: {
              documents: 2,
              occurrences: 1,
              high: 0,
              pending: 1,
              resolved: 0,
              xml_unavailable: 0,
              gross_checked: 123.45,
              high_difference: 0,
            },
            previous: {
              documents: 0,
              occurrences: 0,
              high: 0,
              pending: 0,
              resolved: 0,
              xml_unavailable: 0,
              gross_checked: 0,
              high_difference: 0,
            },
            conformity: {
              clean: 1,
              divergent: 1,
              unmatched_open: 0,
              unmatched_explained: 0,
              posted_outside_period: { count: 0, by_date: [] },
            },
          },
          meta: { branches_unavailable: ["02"] },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const summary = await getEntryAuditSummary("a 1", {
      severity: "Alta",
    });

    expect(summary.kpis.gross_checked).toBe(123.45);
    expect(summary.branches_unavailable).toEqual(["02"]);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/apps/controllership-finance-api/entry-audit/analyses/a%201/summary?severity=Alta",
    );
  });

  it("serializa paginação e filtros da listagem", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: { items: [], page: 2, page_size: 25, total: 0 },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listEntryAuditRows("a1", "occurrences", { branch: "01" }, 2, 25);

    expect(fetchMock.mock.calls[0]?.[0]).toContain(
      "/entry-audit/analyses/a1/occurrences?branch=01&page=2&page_size=25",
    );
  });
});
