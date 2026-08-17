import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { HUB_SECTIONS } from "./pluginRouteCatalog.ts";

describe("hub route badges", () => {
  it("mapeia overdue/today/late e não badgeia Pode faturar", () => {
    const byId = new Map();
    for (const section of HUB_SECTIONS) {
      for (const route of section.routes) {
        byId.set(route.id, route);
      }
    }
    assert.equal(byId.get("tasks_overdue")?.badgeKey, "tasks_overdue");
    assert.equal(byId.get("tasks_today")?.badgeKey, "tasks_today");
    assert.equal(byId.get("orders_late")?.badgeKey, "orders_late");
    assert.equal(byId.get("orders_billable")?.badgeKey, undefined);
  });
});
