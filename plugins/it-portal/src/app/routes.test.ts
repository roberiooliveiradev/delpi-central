import { describe, expect, it } from "vitest";

import { activeNavId, buildPath, normalizeBasePath, resolveRoute } from "./routes";

const BASE = "/apps/it-portal";
const SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f";

describe("resolveRoute", () => {
  it.each([
    [BASE, "home"],
    [`${BASE}/`, "home"],
    [`${BASE}/servers`, "servers"],
    [`${BASE}/workstations`, "workstations"],
    [`${BASE}/action-plans`, "action_plans"],
    [`${BASE}/help`, "help"],
    [`${BASE}/services`, "services"],
    [`${BASE}/databases`, "databases"],
  ])("%s → %s", (pathname, view) => {
    expect(resolveRoute(pathname, BASE).view).toBe(view);
  });

  it("resolves service and database detail with normalized uuids", () => {
    expect(resolveRoute(`${BASE}/services/${SERVER_ID.toUpperCase()}`, BASE)).toEqual({
      view: "service_detail",
      serviceId: SERVER_ID,
    });
    expect(resolveRoute(`${BASE}/databases/${SERVER_ID}`, BASE)).toEqual({
      view: "database_detail",
      databaseId: SERVER_ID,
    });
  });

  it("resolves server detail with a normalized uuid", () => {
    expect(resolveRoute(`${BASE}/servers/${SERVER_ID.toUpperCase()}`, BASE)).toEqual({
      view: "server_detail",
      serverId: SERVER_ID,
    });
    expect(resolveRoute(`${BASE}/workstations/${SERVER_ID.toUpperCase()}`, BASE)).toEqual({
      view: "workstation_detail",
      workstationId: SERVER_ID,
    });
  });

  it.each([
    `${BASE}/servers/not-a-uuid`,
    `${BASE}/workstations/not-a-uuid`,
    `${BASE}/servers/${SERVER_ID}/extra`,
    `${BASE}/monitoring`,
    `${BASE}/action-plans/x`,
    `${BASE}/services/not-a-uuid`,
    `${BASE}/databases/${SERVER_ID}/consumers`,
    `${BASE}/database-instances`,
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
    expect(buildPath(BASE, { serviceId: SERVER_ID })).toBe(`${BASE}/services/${SERVER_ID}`);
    expect(buildPath(BASE, { databaseId: SERVER_ID })).toBe(`${BASE}/databases/${SERVER_ID}`);
    expect(buildPath(BASE, "databases")).toBe(`${BASE}/databases`);
    expect(buildPath(BASE, "workstations")).toBe(`${BASE}/workstations`);
    expect(buildPath(BASE, { workstationId: SERVER_ID })).toBe(`${BASE}/workstations/${SERVER_ID}`);
  });

  it("marks the list active on detail pages and nothing on not found", () => {
    expect(activeNavId("server_detail")).toBe("servers");
    expect(activeNavId("workstation_detail")).toBe("workstations");
    expect(activeNavId("service_detail")).toBe("services");
    expect(activeNavId("database_detail")).toBe("databases");
    expect(activeNavId("not_found")).toBeNull();
  });

  it("normalizes the base path from the host", () => {
    expect(normalizeBasePath(undefined)).toBe(BASE);
    expect(normalizeBasePath("/apps/it-portal/")).toBe(BASE);
  });
});
