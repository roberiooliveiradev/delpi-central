import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const manifestPath = join(
  dirname(fileURLToPath(import.meta.url)),
  "../delpi-mes.manifest.json",
);

describe("delpi-mes.manifest", () => {
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8")) as {
    schemaVersion: string;
    id: string;
    version: string;
    entry: string;
    permissions: Array<{ code: string; name: string; module: string }>;
    routes: Array<{ path: string; permission: string; showInMenu: boolean }>;
    ui?: { renderMode?: string };
  };

  it("keeps schema, id, SemVer and federated entry", () => {
    expect(manifest.schemaVersion).toBe("1.0.0");
    expect(manifest.id).toBe("delpi-mes");
    expect(manifest.version).toMatch(/^\d+\.\d+\.\d+$/);
    expect(manifest.entry).toBe("/apps/delpi-mes/assets/remoteEntry.js");
    expect(manifest.ui?.renderMode).toBe("federated");
  });

  it("declares the downtime-reasons management permission once", () => {
    const codes = manifest.permissions.map((item) => item.code);
    expect(new Set(codes).size).toBe(codes.length);
    expect(codes).toContain("delpi-mes.downtime-reasons.manage");
    expect(manifest.permissions.every((item) => item.module === "delpi-mes")).toBe(true);
  });

  it("declares the registrations routes out of the portal menu", () => {
    const paths = manifest.routes.map((route) => route.path);
    expect(new Set(paths).size).toBe(paths.length);
    const registrations = manifest.routes.find(
      (route) => route.path === "/apps/delpi-mes/registrations",
    );
    const reasons = manifest.routes.find(
      (route) => route.path === "/apps/delpi-mes/registrations/downtime-reasons",
    );
    expect(registrations?.permission).toBe("delpi-mes.downtime-reasons.manage");
    expect(registrations?.showInMenu).toBe(false);
    expect(reasons?.permission).toBe("delpi-mes.downtime-reasons.manage");
    expect(reasons?.showInMenu).toBe(false);
    expect(manifest.routes.filter((route) => route.showInMenu)).toHaveLength(1);
  });

  it("keeps route permissions declared in the manifest", () => {
    const codes = new Set(manifest.permissions.map((item) => item.code));
    for (const route of manifest.routes) {
      expect(codes.has(route.permission)).toBe(true);
    }
  });
});
