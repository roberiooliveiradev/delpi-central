import { describe, expect, it } from "vitest";

import { buildPanelSearchParams, readPanelFilters } from "./panelFilterUrl";

describe("readPanelFilters view mode", () => {
  it("defaults to table", () => {
    expect(readPanelFilters("").view).toBe("table");
  });

  it("maps legacy list to table", () => {
    expect(readPanelFilters("?view=list").view).toBe("table");
  });

  it("parses cards and grouped", () => {
    expect(readPanelFilters("?view=cards").view).toBe("cards");
    expect(readPanelFilters("?view=grouped").view).toBe("grouped");
  });
});

describe("buildPanelSearchParams view mode", () => {
  it("omits default table view from query", () => {
    const params = buildPanelSearchParams({
      branch: "01",
      anchorType: "",
      role: "",
      status: "",
      search: "",
      view: "table",
      groupBy: "work_center",
      page: 1,
    });
    expect(params.get("view")).toBeNull();
  });

  it("persists cards view in query", () => {
    const params = buildPanelSearchParams({
      branch: "01",
      anchorType: "",
      role: "",
      status: "",
      search: "",
      view: "cards",
      groupBy: "work_center",
      page: 1,
    });
    expect(params.get("view")).toBe("cards");
  });
});
