import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const manifestPath = join(dirname(fileURLToPath(import.meta.url)), "../../supplies.manifest.json");

describe("supplies.manifest", () => {
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8")) as {
    schemaVersion: string;
    id: string;
    permissions: Array<{ code: string }>;
    routes: Array<{ path: string; permission: string; showInMenu: boolean }>;
    ui?: { renderMode?: string };
  };

  it("uses Core schemaVersion 1.0.0 and federated entry", () => {
    expect(manifest.schemaVersion).toBe("1.0.0");
    expect(manifest.id).toBe("supplies");
    expect(manifest.ui?.renderMode).toBe("federated");
  });

  it("does not invent CRUD permission codes", () => {
    const codes = manifest.permissions.map((item) => item.code);
    expect(codes).toContain("supplies.portal.access");
    expect(codes.some((code) => /\.(view|write|create|delete)$/.test(code))).toBe(false);
  });

  it("registers launcher plus internal P0 routes without blocked BIs", () => {
    const paths = manifest.routes.map((route) => route.path);
    expect(paths).toContain("/apps/supplies");
    expect(paths).toContain("/apps/supplies/help");
    expect(paths).not.toContain("/apps/supplies/imports");
    expect(paths).not.toContain("/apps/supplies/approvals");
    expect(manifest.routes.filter((route) => route.showInMenu)).toHaveLength(1);
  });
});
