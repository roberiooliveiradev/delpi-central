import { describe, expect, it } from "vitest";

import {
  pickOnboardingShortcuts,
  resolveHomePathSections,
  resolveHubSections,
} from "../../content/pluginRouteCatalog";
import { toHubCapabilities } from "./homeCatalog";

const PORTAL_ONLY = toHubCapabilities({
  portal: true,
  purchaseRequests: false,
  operations: false,
  analytics: false,
  administration: false,
  viewAll: false,
  export: false,
});

const WITH_ANALYTICS = {
  ...PORTAL_ONLY,
  analytics: true,
};

describe("Home catalog", () => {
  it("omits overview without analytics capability", () => {
    const ids = resolveHomePathSections(PORTAL_ONLY).flatMap((section) =>
      section.routes.map((route) => route.id),
    );
    expect(ids).not.toContain("overview");
    expect(ids).toContain("help");
    expect(ids).toContain("my_tasks");
    expect(ids).not.toContain("home");
  });

  it("includes overview as sibling when analytics is granted", () => {
    const ids = resolveHomePathSections(WITH_ANALYTICS).flatMap((section) =>
      section.routes.map((route) => route.id),
    );
    expect(ids).toContain("overview");
  });

  it("does not use roles — only capability flags", () => {
    const caps = toHubCapabilities({
      portal: true,
      purchaseRequests: true,
      operations: false,
      analytics: false,
      administration: false,
      viewAll: false,
      export: false,
    });
    const sections = resolveHubSections(caps);
    const ids = sections.flatMap((section) => section.routes.map((route) => route.id));
    expect(ids).toContain("purchase_requests");
    expect(ids).not.toContain("purchase_orders");
  });

  it("picks up to three onboarding shortcuts by capability", () => {
    const portalOnly = pickOnboardingShortcuts(PORTAL_ONLY);
    expect(portalOnly.map((route) => route.id)).toEqual(["my_tasks", "help"]);

    const full = pickOnboardingShortcuts({
      analytics: true,
      purchaseRequests: true,
      operations: true,
      administration: true,
    });
    expect(full).toHaveLength(3);
    expect(full[0]?.id).toBe("purchase_requests");
    expect(full[1]?.id).toBe("overview");
  });
});
