import { describe, expect, it } from "vitest";

import {
  buildPanelPath,
  buildPanelSearchParams,
  readPanelFilters,
} from "./panelFilterUrl";

describe("panelFilterUrl", () => {
  it("reads default filters from empty search", () => {
    expect(readPanelFilters("")).toMatchObject({
      branch: "01",
      view: "list",
      groupBy: "work_center",
      page: 1,
    });
  });

  it("round-trips query params", () => {
    const search =
      "?branch=02&status=online&role=pulse_counter&search=esp&view=grouped&groupBy=machine&page=2";
    const filters = readPanelFilters(search);
    expect(filters.branch).toBe("02");
    expect(filters.status).toBe("online");
    expect(filters.role).toBe("pulse_counter");
    expect(filters.search).toBe("esp");
    expect(filters.view).toBe("grouped");
    expect(filters.groupBy).toBe("machine");
    expect(filters.page).toBe(2);
    expect(buildPanelSearchParams(filters).toString()).toContain("branch=02");
    expect(buildPanelPath(filters)).toContain("/apps/production-pulse?");
  });
});
