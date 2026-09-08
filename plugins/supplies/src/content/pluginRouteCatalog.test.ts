import { describe, expect, it } from "vitest";

import {
  collectSearchHits,
  HUB_SECTIONS,
  resolveHubSections,
} from "./pluginRouteCatalog";
import { resolveShellNavItems } from "./shellNav";

const ALL_CAPS = {
  analytics: true,
  purchaseRequests: true,
  operations: true,
  administration: true,
};

const PORTAL_ONLY = {
  analytics: false,
  purchaseRequests: false,
  operations: false,
  administration: false,
};

describe("routeCatalog", () => {
  it("keeps portal routes and omits analytics without cap", () => {
    const sections = resolveHubSections(PORTAL_ONLY);
    const ids = sections.flatMap((section) => section.routes.map((route) => route.id));
    expect(ids).toContain("home");
    expect(ids).toContain("help");
    expect(ids).not.toContain("overview");
    expect(ids).not.toContain("purchase_requests");
  });

  it("shows sibling operations routes together", () => {
    const sections = resolveHubSections({
      ...PORTAL_ONLY,
      operations: true,
    });
    const ids = sections.flatMap((section) => section.routes.map((route) => route.id));
    expect(ids).toContain("purchase_orders");
    expect(ids).toContain("safety_stock");
    expect(ids).not.toContain("administration");
  });

  it("does not include blocked imports/approvals routes", () => {
    const ids = HUB_SECTIONS.flatMap((section) => section.routes.map((route) => route.id));
    expect(ids).not.toContain("imports");
    expect(ids).not.toContain("approvals");
  });

  it("filters shell nav by capability", () => {
    const items = resolveShellNavItems(PORTAL_ONLY).map((item) => item.id);
    expect(items).toEqual(["home", "my_tasks", "help"]);
    const full = resolveShellNavItems(ALL_CAPS).map((item) => item.id);
    expect(full).toContain("overview");
    expect(full).toContain("purchase_requests");
  });

  it("ranks palette hits from the filtered catalog", () => {
    const hits = collectSearchHits(resolveHubSections(ALL_CAPS), "sc");
    expect(hits.some((hit) => hit.id === "purchase_requests")).toBe(true);
  });
});
