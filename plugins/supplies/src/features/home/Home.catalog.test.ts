import { describe, expect, it } from "vitest";

import {
  pickOnboardingShortcuts,
  resolveHomePathSections,
  resolveHubSections,
} from "../../content/pluginRouteCatalog";
import { toHubCapabilities } from "./homeCatalog";

const NO_ACCESS = toHubCapabilities({
  access: false,
  manage: false,
  viewAll: false,
});

const WITH_ACCESS = toHubCapabilities({
  access: true,
  manage: false,
  viewAll: false,
});

describe("Home catalog", () => {
  it("omits product sections without access", () => {
    const ids = resolveHomePathSections(NO_ACCESS).flatMap((section) =>
      section.routes.map((route) => route.id),
    );
    expect(ids).not.toContain("overview");
    expect(ids).toContain("help");
    expect(ids).not.toContain("home");
  });

  it("includes overview when access is granted", () => {
    const ids = resolveHomePathSections(WITH_ACCESS).flatMap((section) =>
      section.routes.map((route) => route.id),
    );
    expect(ids).toContain("overview");
  });

  it("does not use roles — access opens normal sections and manage opens admin", () => {
    const caps = toHubCapabilities({
      access: true,
      manage: false,
      viewAll: false,
    });
    const sections = resolveHubSections(caps);
    const ids = sections.flatMap((section) => section.routes.map((route) => route.id));
    expect(ids).toContain("purchase_requests");
    expect(ids).toContain("purchase_orders");
    expect(ids).not.toContain("administration");
  });

  it("picks up to three onboarding shortcuts by capability", () => {
    const portalOnly = pickOnboardingShortcuts(NO_ACCESS);
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
