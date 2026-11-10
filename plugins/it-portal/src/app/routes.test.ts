import { describe, expect, it } from "vitest";

import { activeNavId, buildPath, normalizeBasePath, resolveRoute } from "./routes";

const BASE = "/apps/it-portal";
const SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f";

describe("resolveRoute", () => {
  it.each([
    [BASE, "home"],
    [`${BASE}/`, "home"],
    [`${BASE}/servers`, "servers"],
    [`${BASE}/action-plans`, "action_plans"],
    [`${BASE}/help`, "help"],
  ])("%s → %s", (pathname, view) => {
    expect(resolveRoute(pathname, BASE).view).toBe(view);
  });

  it("resolves server detail with a normalized uuid", () => {
    expect(resolveRoute(`${BASE}/servers/${SERVER_ID.toUpperCase()}`, BASE)).toEqual({
      view: "server_detail",
      serverId: SERVER_ID,
    });
  });

  it.each([
    `${BASE}/servers/not-a-uuid`,
    `${BASE}/servers/${SERVER_ID}/extra`,
    `${BASE}/monitoring`,
    `${BASE}/action-plans/x`,
    "/apps/other",
    "/apps/it-portalx",
  ])("does not invent pages for %s", (pathname) => {
    expect(resolveRoute(pathname, BASE).view).toBe("not_found");
  });
});

describe("navigation helpers", () => {
  it("builds paths under the host base path", () => {
    expect(buildPath(BASE, "home")).toBe(BASE);
    expect(buildPath(BASE, "action_plans")).toBe(`${BASE}/action-plans`);
    expect(buildPath(BASE, { serverId: SERVER_ID })).toBe(`${BASE}/servers/${SERVER_ID}`);
  });

  it("marks servers active on the detail page and nothing on not found", () => {
    expect(activeNavId("server_detail")).toBe("servers");
    expect(activeNavId("not_found")).toBeNull();
  });

  it("normalizes the base path from the host", () => {
    expect(normalizeBasePath(undefined)).toBe(BASE);
    expect(normalizeBasePath("/apps/it-portal/")).toBe(BASE);
  });
});
