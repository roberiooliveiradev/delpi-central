import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { resolveRoute } from "./app/routes";

type Manifest = {
  id: string;
  basePath: string;
  entry: string;
  permissions: { code: string; module: string }[];
  routes: { path: string; permission: string }[];
  ui: { renderMode: string };
};

const manifest = JSON.parse(
  readFileSync(path.resolve(__dirname, "../it-portal.manifest.json"), "utf8"),
) as Manifest;

/** Espelho do contrato da BFF (`it_portal_app/interface/http/authz.py`). */
const BFF_PERMISSIONS = [
  "it-portal.access",
  "it-portal.servers.view",
  "it-portal.servers.manage",
  "it-portal.notes.create",
  "it-portal.actions.view",
  "it-portal.actions.manage",
];

describe("it-portal manifest", () => {
  it("declares exactly the permissions enforced by the BFF", () => {
    expect(manifest.permissions.map((p) => p.code).sort()).toEqual([...BFF_PERMISSIONS].sort());
    expect(manifest.permissions.every((p) => p.module === "it-portal")).toBe(true);
  });

  it("is a federated remote under its own base path", () => {
    expect(manifest.id).toBe("it-portal");
    expect(manifest.basePath).toBe("/apps/it-portal");
    expect(manifest.entry).toBe("/apps/it-portal/assets/remoteEntry.js");
    expect(manifest.ui.renderMode).toBe("federated");
  });

  it("only registers routes the MFE actually implements", () => {
    for (const route of manifest.routes) {
      expect(BFF_PERMISSIONS).toContain(route.permission);
      expect(resolveRoute(route.path, manifest.basePath).view).not.toBe("not_found");
    }
  });
});
