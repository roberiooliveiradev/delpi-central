import { describe, expect, it } from "vitest";

import { sameDeliveriesQuery, parseQueryFromSearch, buildUrlSearch } from "./query";
import type { DeliveriesQuery } from "./types";

describe("deliveries URL popstate rehydration (pure)", () => {
  it("state A → B → popstate A restaura query A", () => {
    const stateA: DeliveriesQuery = parseQueryFromSearch(
      "?branch=01&status=late&start_date=2026-09-01&end_date=2026-09-15&page=1&page_size=20",
      ["01", "02"],
    );
    const stateB: DeliveriesQuery = parseQueryFromSearch(
      "?branch=02&status=on_time&start_date=2026-08-01&end_date=2026-08-31&page=2&page_size=50&sort_by=days_diff&sort_dir=desc",
      ["01", "02"],
    );
    expect(sameDeliveriesQuery(stateA, stateB)).toBe(false);

    // Simulate popstate restoring URL A
    const restored = parseQueryFromSearch(buildUrlSearch(stateA), ["01", "02"]);
    expect(sameDeliveriesQuery(restored, stateA)).toBe(true);
    expect(buildUrlSearch(restored)).not.toContain("branch=02");
  });
});
