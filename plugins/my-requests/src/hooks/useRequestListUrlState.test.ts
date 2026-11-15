import { describe, expect, it } from "vitest";

import type { RequestListFiltersState } from "../content/requestListFilters";
import {
  requestListFiltersFromSearch,
  requestListFiltersToSearch,
} from "./useRequestListUrlState";

const DEFAULTS: RequestListFiltersState = {
  q: "",
  typeCode: "",
  status: "",
  branch: "",
  mineScope: "",
  sort: "",
  page: 1,
  pageSize: 20,
};

describe("useRequestListUrlState — serialização", () => {
  it("defaults não poluem a URL", () => {
    expect(requestListFiltersToSearch(DEFAULTS)).toBe("");
  });

  it("serializa só valores não-default (q/type/status/branch/scope/sort/page)", () => {
    const search = requestListFiltersToSearch({
      q: "nota",
      typeCode: "invoice-issuance",
      status: "submitted",
      branch: "filial-01",
      mineScope: "assigned_to_me",
      sort: "status:asc,created_at:desc",
      page: 3,
      pageSize: 20,
    });
    const params = new URLSearchParams(search.slice(1));
    expect(params.get("q")).toBe("nota");
    expect(params.get("type")).toBe("invoice-issuance");
    expect(params.get("status")).toBe("submitted");
    expect(params.get("branch")).toBe("filial-01");
    expect(params.get("mine_scope")).toBe("assigned_to_me");
    expect(params.get("sort")).toBe("status:asc,created_at:desc");
    expect(params.get("page")).toBe("3");
    expect(params.get("page_size")).toBeNull();
  });

  it("page_size entra na URL só quando difere do default e volta no parse", () => {
    const search = requestListFiltersToSearch({ ...DEFAULTS, pageSize: 50 });
    const params = new URLSearchParams(search.slice(1));
    expect(params.get("page_size")).toBe("50");
    expect(
      requestListFiltersFromSearch(search, DEFAULTS).pageSize,
    ).toBe(50);
  });

  it("round-trip preserva filtros e página", () => {
    const filters: RequestListFiltersState = {
      q: "abc",
      typeCode: "general-request",
      status: "in_progress",
      branch: "filial-02",
      mineScope: "completed_by_me",
      sort: "created_at:asc",
      page: 2,
      pageSize: 50,
    };
    expect(
      requestListFiltersFromSearch(
        requestListFiltersToSearch(filters),
        DEFAULTS,
      ),
    ).toEqual(filters);
  });
});

describe("useRequestListUrlState — parse defensivo", () => {
  it("URL vazia herda todos os defaults", () => {
    expect(requestListFiltersFromSearch("", DEFAULTS)).toEqual(DEFAULTS);
    expect(requestListFiltersFromSearch("?", DEFAULTS)).toEqual(DEFAULTS);
  });

  it("mine_scope inválido cai no default", () => {
    expect(
      requestListFiltersFromSearch("?mine_scope=hack", DEFAULTS).mineScope,
    ).toBe("");
    expect(
      requestListFiltersFromSearch(
        "?mine_scope=completed_by_me",
        DEFAULTS,
      ).mineScope,
    ).toBe("completed_by_me");
  });

  it("page inválida/zero/negativa cai para 1", () => {
    for (const raw of ["?page=abc", "?page=0", "?page=-3"]) {
      expect(requestListFiltersFromSearch(raw, DEFAULTS).page).toBe(1);
    }
  });

  it("page_size fora das opções cai no default", () => {
    for (const raw of ["?page_size=abc", "?page_size=13", "?page_size=999"]) {
      expect(requestListFiltersFromSearch(raw, DEFAULTS).pageSize).toBe(20);
    }
    for (const size of [10, 50, 100]) {
      expect(
        requestListFiltersFromSearch(`?page_size=${size}`, DEFAULTS).pageSize,
      ).toBe(size);
    }
  });

  it("campos ausentes herdam defaults da página, não vazios fixos", () => {
    const defaults: RequestListFiltersState = {
      ...DEFAULTS,
      status: "submitted",
      sort: "status:asc",
    };
    const parsed = requestListFiltersFromSearch("?q=x", defaults);
    expect(parsed.q).toBe("x");
    expect(parsed.status).toBe("submitted");
    expect(parsed.sort).toBe("status:asc");
  });
});
