import { describe, expect, it } from "vitest";

import { buildPpcHref, parsePpcPath } from "./routeParser";

describe("parsePpcPath", () => {
  it("defaults empty base path to home", () => {
    const route = parsePpcPath("/apps/production-control", "", "01");
    expect(route.subpluginId).toBe("home");
    expect(route.branch).toBe("01");
    expect(route.issueId).toBeNull();
  });

  it("reads issue and branch from query", () => {
    const route = parsePpcPath(
      "/apps/production-control/problem-analysis",
      "?branch=02&issue=delayed-order:01%7CA",
      "01",
    );
    expect(route.subpluginId).toBe("problem-analysis");
    expect(route.branch).toBe("02");
    expect(route.issueId).toBe("delayed-order:01|A");
  });

  it("reads work center and scheduling window from query", () => {
    const route = parsePpcPath(
      "/apps/production-control/machine-load",
      "?branch=01&ct=CT-02&startDate=2026-08-24&endDate=2026-08-28",
      "02",
    );
    expect(route.subpluginId).toBe("machine-load");
    expect(route.workCenter).toBe("CT-02");
    expect(route.startDate).toBe("2026-08-24");
    expect(route.endDate).toBe("2026-08-28");
  });

  it("ignores malformed dates instead of forwarding them to the API", () => {
    const route = parsePpcPath(
      "/apps/production-control/machine-load",
      "?branch=01&startDate=24%2F08%2F2026&endDate=",
      "01",
    );
    expect(route.startDate).toBeNull();
    expect(route.endDate).toBeNull();
  });
});

describe("buildPpcHref", () => {
  it("keeps home on the plugin base path", () => {
    expect(buildPpcHref({ subpluginId: "home", branch: "01" })).toBe(
      "/apps/production-control?branch=01",
    );
  });

  it("serializes deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "problem-analysis",
        branch: "01",
        issueId: "delayed-order:01|A",
      }),
    ).toBe("/apps/production-control/problem-analysis?branch=01&issue=delayed-order%3A01%7CA");
  });

  it("keeps the work center tab and the period in the deep link", () => {
    expect(
      buildPpcHref({
        subpluginId: "machine-load",
        branch: "02",
        workCenter: "CT-02",
        startDate: "2026-08-24",
        endDate: "2026-08-28",
      }),
    ).toBe(
      "/apps/production-control/machine-load?branch=02&ct=CT-02&startDate=2026-08-24&endDate=2026-08-28",
    );
  });
});
