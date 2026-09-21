import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { AppItem } from "../data/coreApi.ts";
import {
  buildGlobalDeliaHostProps,
  findAuthorizedDeliaApp,
  isDeliaFullPagePath,
  shouldKeepGlobalDeliaPanelOpen,
  shouldRenderGlobalDeliaLauncher,
} from "./globalDeliaSurface.ts";

function deliaApp(overrides: Partial<AppItem> = {}): AppItem {
  return {
    id: "delia",
    name: "DÉLIA",
    basePath: "/apps/delia",
    type: "microfrontend",
    renderMode: "federated",
    entryUrl: "/apps/delia/assets/remoteEntry.js",
    routes: [
      {
        app: "delia",
        path: "/apps/delia",
        label: "DÉLIA",
        permission: "delia.access",
      },
    ],
    ...overrides,
  };
}

function helpdeskApp(): AppItem {
  return {
    id: "helpdesk",
    name: "Helpdesk",
    basePath: "/apps/helpdesk",
    type: "microfrontend",
    renderMode: "federated",
    entryUrl: "/apps/helpdesk/assets/remoteEntry.js",
    routes: [
      {
        app: "helpdesk",
        path: "/apps/helpdesk",
        label: "Helpdesk",
        permission: "helpdesk.access",
      },
    ],
  };
}

describe("authorized discovery", () => {
  it("encontra DÉLIA apenas pelo id do /me/apps", () => {
    assert.equal(findAuthorizedDeliaApp([helpdeskApp(), deliaApp()])?.id, "delia");
    assert.equal(shouldRenderGlobalDeliaLauncher({
      apps: [deliaApp()],
      pathname: "/apps/helpdesk",
    }), true);
  });

  it("não inventa DÉLIA a partir de permissions/isSuperadmin", () => {
    const apps = [helpdeskApp()];
    assert.equal(findAuthorizedDeliaApp(apps), null);
    assert.equal(
      shouldRenderGlobalDeliaLauncher({
        apps,
        pathname: "/",
      }),
      false,
    );
    assert.equal(
      shouldKeepGlobalDeliaPanelOpen({
        apps,
        pathname: "/",
        requestedOpen: true,
      }),
      false,
    );
  });

  it("omite o launcher quando DÉLIA não está no catálogo Core", () => {
    assert.equal(findAuthorizedDeliaApp([]), null);
    assert.equal(findAuthorizedDeliaApp(undefined), null);
  });
});

describe("full-page safety", () => {
  it("esconde o launcher na rota full-page da DÉLIA e filhos", () => {
    assert.equal(isDeliaFullPagePath("/apps/delia", "/apps/delia"), true);
    assert.equal(isDeliaFullPagePath("/apps/delia/inbox", "/apps/delia"), true);
    assert.equal(isDeliaFullPagePath("/apps/helpdesk", "/apps/delia"), false);
    assert.equal(
      shouldRenderGlobalDeliaLauncher({
        apps: [deliaApp()],
        pathname: "/apps/delia",
      }),
      false,
    );
    assert.equal(
      shouldKeepGlobalDeliaPanelOpen({
        apps: [deliaApp()],
        pathname: "/apps/delia",
        requestedOpen: true,
      }),
      false,
    );
  });
});

describe("session teardown", () => {
  it("fecha o painel quando o catálogo autenticado perde DÉLIA", () => {
    assert.equal(
      shouldKeepGlobalDeliaPanelOpen({
        apps: [],
        pathname: "/",
        requestedOpen: true,
      }),
      false,
    );
  });
});

describe("global host props", () => {
  it("não inventa routeLabel de outro app nem contexto operacional", () => {
    const props = buildGlobalDeliaHostProps({
      app: deliaApp(),
      pathname: "/apps/helpdesk",
      search: "?op=123",
      getAccessToken: () => undefined,
      user: { permissions: ["delia.access"], is_superadmin: true },
    });

    assert.equal(props.basePath, "/apps/delia");
    assert.equal(props.pathname, "/apps/helpdesk");
    assert.equal(props.search, "?op=123");
    assert.equal(props.routeLabel, undefined);
    assert.equal(props.alternateEntry, undefined);
    assert.deepEqual(props.appRoutes, [
      { path: "/apps/delia", entry: null, openInNewTab: false },
    ]);
    assert.deepEqual(props.permissions, ["delia.access"]);
    assert.equal(props.isSuperadmin, true);
  });

  it("só preenche routeLabel quando o path atual é rota da DÉLIA", () => {
    const props = buildGlobalDeliaHostProps({
      app: deliaApp(),
      pathname: "/apps/delia",
      search: "",
      getAccessToken: () => undefined,
      user: null,
    });
    assert.equal(props.routeLabel, "DÉLIA");
  });
});
