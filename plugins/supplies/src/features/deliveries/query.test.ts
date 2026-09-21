import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { listLateDeliveries } from "./api";
import { mapDeliveriesFetchError } from "./content";
import { hasActiveDeliveriesFilters } from "./hasActiveFilters";
import {
  buildListSearchParams,
  buildUrlSearch,
  createDefaultQuery,
  nextServerSort,
  parseQueryFromSearch,
} from "./query";

describe("deliveries query / API params", () => {
  it("default = Todas + late + mês corrente (até hoje no preset this_month)", () => {
    const fixed = new Date("2026-09-15T12:00:00-03:00");
    const q = createDefaultQuery([], fixed);
    expect(q.branches).toEqual([]);
    expect(q.status).toBe("late");
    expect(q.start_date).toBe("2026-09-01");
    expect(q.end_date).toBe("2026-09-15");
    expect(q.page).toBe(1);
    expect(q.page_size).toBe(20);
  });

  it("Todas omite branch; unidade única envia branch", () => {
    const all = createDefaultQuery();
    const paramsAll = buildListSearchParams(all);
    expect(paramsAll.getAll("branch")).toEqual([]);
    expect(paramsAll.get("status")).toBe("late");

    const single = { ...all, branches: ["01"] };
    const paramsSingle = buildListSearchParams(single);
    expect(paramsSingle.getAll("branch")).toEqual(["01"]);
  });

  it("não emite branch=all nem consolidado", () => {
    const qs = buildListSearchParams(createDefaultQuery()).toString();
    expect(qs).not.toMatch(/branch=all/);
    expect(qs).not.toMatch(/consolidated/);
  });

  it("envia sort e paginação server-side", () => {
    const q = {
      ...createDefaultQuery(),
      sort_by: "days_diff",
      sort_dir: "desc" as const,
      page: 2,
      page_size: 50,
    };
    const params = buildListSearchParams(q);
    expect(params.get("sort_by")).toBe("days_diff");
    expect(params.get("sort_dir")).toBe("desc");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("50");
  });

  it("URL state round-trip preserva filtros P0", () => {
    const query = {
      branches: ["02"],
      status: "on_time" as const,
      start_date: "2026-08-01",
      end_date: "2026-08-31",
      sort_by: "receipt_entry_date",
      sort_dir: "desc" as const,
      page: 3,
      page_size: 50,
    };
    const search = buildUrlSearch(query);
    const parsed = parseQueryFromSearch(search, ["01", "02"]);
    expect(parsed).toEqual(query);
  });

  it("deep-link F5-equivalent parse completo", () => {
    const search =
      "?branch=01&status=on_time&start_date=2026-09-01&end_date=2026-09-30&page=2&page_size=20&sort_by=expected_delivery_date&sort_dir=desc";
    const parsed = parseQueryFromSearch(search, ["01", "02"]);
    expect(parsed).toEqual({
      branches: ["01"],
      status: "on_time",
      start_date: "2026-09-01",
      end_date: "2026-09-30",
      page: 2,
      page_size: 20,
      sort_by: "expected_delivery_date",
      sort_dir: "desc",
    });
    expect(buildUrlSearch(parsed)).toContain("branch=01");
    expect(buildUrlSearch(parsed)).not.toContain("branch=02");
  });

  it("sanitiza params inválidos sem inventar branch", () => {
    const parsed = parseQueryFromSearch(
      "?status=garbage&branch=99&page=-1&page_size=abc&sort_dir=x&sort_by=unknown",
      ["01", "02"],
    );
    expect(parsed.status).toBe("late");
    expect(parsed.branches).toEqual([]);
    expect(parsed.page).toBe(1);
    expect(parsed.page_size).toBe(20);
    expect(parsed.sort_dir).toBe("asc");
    expect(parsed.sort_by).toBe("");
  });

  it("filtro muda com page=1 na query URL ao reparsear após patch mental", () => {
    const base = createDefaultQuery([], new Date("2026-09-15T12:00:00-03:00"));
    const patched = { ...base, status: "on_time" as const, page: 1 };
    expect(patched.page).toBe(1);
    expect(buildListSearchParams(patched).get("status")).toBe("on_time");
  });

  it("sort troca direção e reseta page=1", () => {
    const current = {
      ...createDefaultQuery(),
      sort_by: "status",
      sort_dir: "asc" as const,
      page: 4,
    };
    expect(nextServerSort(current, "status")).toEqual({
      sort_by: "status",
      sort_dir: "desc",
      page: 1,
    });
    expect(nextServerSort(current, "days_diff")).toEqual({
      sort_by: "days_diff",
      sort_dir: "asc",
      page: 1,
    });
  });

  it("troca de filtro marca active e clear volta ao default", () => {
    const fixed = new Date("2026-09-15T12:00:00-03:00");
    const defaults = createDefaultQuery([], fixed);
    expect(hasActiveDeliveriesFilters(defaults, ["01", "02"], fixed)).toBe(false);
    expect(
      hasActiveDeliveriesFilters(
        { ...defaults, branches: ["01"] },
        ["01", "02"],
        fixed,
      ),
    ).toBe(true);
    expect(
      hasActiveDeliveriesFilters(
        { ...defaults, status: "on_time" },
        ["01", "02"],
        fixed,
      ),
    ).toBe(true);
  });
});

describe("listLateDeliveries client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("chama GET /apps/supplies-api/deliveries/late com query correta", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0,
        summary: { total_lines: 0, late_lines: 0, on_time_lines: 0 },
      }),
    });

    await listLateDeliveries({
      branches: [],
      status: "late",
      start_date: "2026-09-01",
      end_date: "2026-09-30",
      sort_by: "days_diff",
      sort_dir: "asc",
      page: 1,
      page_size: 20,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toMatch(/^\/apps\/supplies-api\/deliveries\/late\?/);
    expect(url).not.toMatch(/branch=/);
    expect(url).toMatch(/status=late/);
    expect(url).toMatch(/start_date=2026-09-01/);
    expect(url).toMatch(/end_date=2026-09-30/);
    expect(url).toMatch(/sort_by=days_diff/);
    expect(url).toMatch(/page=1/);
    expect(url).not.toMatch(/api-delpi/);
  });

  it("single branch envia branch=01", async () => {
    const fetchMock = globalThis.fetch as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        page: 1,
        page_size: 20,
        total: 0,
      }),
    });

    await listLateDeliveries({
      ...createDefaultQuery([], new Date("2026-09-15T12:00:00-03:00")),
      branches: ["01"],
    });

    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toMatch(/branch=01/);
    expect(url).not.toMatch(/branch=02/);
  });
});

describe("deliveries error mapping", () => {
  it("403 → mensagem de filial/módulo sem inventar permission de entregas", () => {
    const mapped = mapDeliveriesFetchError("Erro HTTP 403");
    expect(mapped).toMatch(/filial|módulo/i);
    expect(mapped).not.toMatch(/deliveries/i);
    expect(mapped).not.toMatch(/permission de entregas/i);
  });
});
