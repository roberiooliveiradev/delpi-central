import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  resolveAuthorizedEntryPath,
  resolveManifestRoutePermission,
} from "./manifestRoutePermission.ts";

const CATALOG = [
  { app: "cf", path: "/apps/controllership-finance", permission: "controllership-finance.access", showInMenu: true },
  { app: "cf", path: "/apps/controllership-finance/closing/admin", permission: "controllership-finance.manage", showInMenu: false },
  { app: "cf", path: "/apps/controllership-finance/closing/monthly-closing", permission: "controllership-finance.access", showInMenu: false },
  { app: "cf", path: "/apps/controllership-finance/closing/documents", permission: "controllership-finance.access.dre", showInMenu: false },
];

describe("resolveManifestRoutePermission", () => {
  it("rota raiz exige access — audiência DRE não entra pela raiz", () => {
    assert.equal(
      resolveManifestRoutePermission(CATALOG as never, "/apps/controllership-finance"),
      "controllership-finance.access",
    );
  });

  it("rota dedicada resolve a capability documental", () => {
    assert.equal(
      resolveManifestRoutePermission(
        CATALOG as never,
        "/apps/controllership-finance/closing/documents",
      ),
      "controllership-finance.access.dre",
    );
  });

  it("rota interna mais específica prevalece sobre o prefixo genérico", () => {
    assert.equal(
      resolveManifestRoutePermission(
        CATALOG as never,
        "/apps/controllership-finance/closing/admin/users",
      ),
      "controllership-finance.manage",
    );
  });
});

describe("resolveAuthorizedEntryPath", () => {
  it("DRE read-only no basePath entra pela única rota autorizada", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      resolveAuthorizedEntryPath(
        dre as never,
        "/apps/controllership-finance",
        "/apps/controllership-finance",
      ),
      "/apps/controllership-finance/closing/documents",
    );
  });

  it("prefere a primeira rota visível no menu, como o launcher", () => {
    const user = [
      { app: "cf", path: "/apps/controllership-finance/closing/other", showInMenu: false },
      { app: "cf", path: "/apps/controllership-finance/closing/documents", showInMenu: true },
    ];
    assert.equal(
      resolveAuthorizedEntryPath(
        user as never,
        "/apps/controllership-finance",
        "/apps/controllership-finance",
      ),
      "/apps/controllership-finance/closing/documents",
    );
  });

  it("basePath com barra final resolve igual", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      resolveAuthorizedEntryPath(
        dre as never,
        "/apps/controllership-finance/",
        "/apps/controllership-finance",
      ),
      "/apps/controllership-finance/closing/documents",
    );
  });

  it("rota interna negada NÃO redireciona — /unauthorized é a negação", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      resolveAuthorizedEntryPath(
        dre as never,
        "/apps/controllership-finance/closing/monthly-closing",
        "/apps/controllership-finance",
      ),
      undefined,
    );
  });

  it("sem rota autorizada ou fora do basePath retorna undefined", () => {
    assert.equal(
      resolveAuthorizedEntryPath([], "/apps/controllership-finance", "/apps/controllership-finance"),
      undefined,
    );
    assert.equal(
      resolveAuthorizedEntryPath([CATALOG[3]] as never, "/apps/controllership-finance/x", "/apps/controllership-finance"),
      undefined,
    );
    assert.equal(
      resolveAuthorizedEntryPath([CATALOG[3]] as never, "/apps/other", "/apps/controllership-finance"),
      undefined,
    );
  });

  it("entrada igual ao path atual retorna undefined — sem loop", () => {
    const only = [{ app: "x", path: "/apps/x", permission: "x.read", showInMenu: true }];
    assert.equal(
      resolveAuthorizedEntryPath(only as never, "/apps/x", "/apps/x"),
      undefined,
    );
  });
});
