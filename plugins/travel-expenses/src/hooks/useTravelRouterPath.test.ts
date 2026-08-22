import { describe, expect, it } from "vitest";

import { parseTravelRoute, readListSearch } from "./useTravelRouterPath";

describe("parseTravelRoute", () => {
  it("parses hub, list, new, detail and package", () => {
    expect(parseTravelRoute("/apps/travel-expenses")).toEqual({ kind: "hub" });
    expect(parseTravelRoute("/apps/travel-expenses/reports", "?scope=unit")).toEqual({
      kind: "list",
      scope: "unit",
    });
    expect(parseTravelRoute("/apps/travel-expenses/reports/new")).toEqual({ kind: "new" });
    expect(parseTravelRoute("/apps/travel-expenses/reports/abc")).toEqual({
      kind: "detail",
      reportId: "abc",
    });
    expect(parseTravelRoute("/apps/travel-expenses/reports/abc/package")).toEqual({
      kind: "package",
      reportId: "abc",
    });
  });
});

describe("readListSearch", () => {
  it("reads shareable filters", () => {
    expect(readListSearch("?scope=unit&unit=01&q=SP&from=2026-08-01&to=2026-08-22")).toEqual({
      scope: "unit",
      unit: "01",
      q: "SP",
      periodFrom: "2026-08-01",
      periodTo: "2026-08-22",
    });
  });
});
