import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  hasAuthorizedAppEntry,
  resolveManifestRoutePermission,
} from "./manifestRoutePermission.ts";

const CATALOG = [
  { app: "cf", path: "/apps/controllership-finance", permission: "controllership-finance.access", showInMenu: true },
  { app: "cf", path: "/apps/controllership-finance/closing/admin", permission: "controllership-finance.manage", showInMenu: false },
  { app: "cf", path: "/apps/controllership-finance/closing/monthly-closing", permission: "controllership-finance.access", showInMenu: false },
  { app: "cf", path: "/apps/controllership-finance/closing/documents", permission: "controllership-finance.access.dre", showInMenu: false },
];

describe("resolveManifestRoutePermission", () => {
  it("rota raiz exige access — DRE entra pelo mount no basePath, não pela permission", () => {
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

describe("hasAuthorizedAppEntry", () => {
  it("DRE read-only no basePath monta o app — a Home única decide", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      hasAuthorizedAppEntry(
        dre as never,
        "/apps/controllership-finance",
        "/apps/controllership-finance",
      ),
      true,
    );
  });

  it("qualquer rota autorizada habilita a entrada — visível ou oculta", () => {
    const user = [
      { app: "cf", path: "/apps/controllership-finance/closing/other", showInMenu: false },
      { app: "cf", path: "/apps/controllership-finance/closing/documents", showInMenu: true },
    ];
    assert.equal(
      hasAuthorizedAppEntry(
        user as never,
        "/apps/controllership-finance",
        "/apps/controllership-finance",
      ),
      true,
    );
    assert.equal(
      hasAuthorizedAppEntry(
        [user[0]] as never,
        "/apps/controllership-finance",
        "/apps/controllership-finance",
      ),
      true,
    );
  });

  it("basePath com barra final resolve igual", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      hasAuthorizedAppEntry(
        dre as never,
        "/apps/controllership-finance/",
        "/apps/controllership-finance",
      ),
      true,
    );
  });

  it("rota interna negada NÃO monta — /unauthorized é a negação", () => {
    const dre = [CATALOG[3]];
    assert.equal(
      hasAuthorizedAppEntry(
        dre as never,
        "/apps/controllership-finance/closing/monthly-closing",
        "/apps/controllership-finance",
      ),
      false,
    );
  });

  it("sem rota autorizada ou fora do basePath retorna false", () => {
    assert.equal(
      hasAuthorizedAppEntry([], "/apps/controllership-finance", "/apps/controllership-finance"),
      false,
    );
    assert.equal(
      hasAuthorizedAppEntry([CATALOG[3]] as never, "/apps/controllership-finance/x", "/apps/controllership-finance"),
      false,
    );
    assert.equal(
      hasAuthorizedAppEntry([CATALOG[3]] as never, "/apps/other", "/apps/controllership-finance"),
      false,
    );
  });

  it("rotas sem path não habilitam a entrada", () => {
    const broken = [{ app: "x", permission: "x.read", showInMenu: true }];
    assert.equal(
      hasAuthorizedAppEntry(broken as never, "/apps/x", "/apps/x"),
      false,
    );
  });
});
