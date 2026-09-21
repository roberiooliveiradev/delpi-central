import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { AppItem } from "../data/coreApi.ts";
import {
  DELIA_DOCK_DEFAULT_WIDTH,
  DELIA_DOCK_MAX_WIDTH,
  DELIA_DOCK_MIN_WIDTH,
  adjustDeliaDockWidth,
  buildGlobalDeliaHostProps,
  clampDeliaDockWidth,
  findAuthorizedDeliaApp,
  isDeliaFullPagePath,
  resolveDeliaDockMaxWidth,
  resolveFocusReturnTarget,
  shouldKeepCompanionDockOpen,
  shouldRenderCompanionHandle,
} from "./globalDeliaDock.ts";

const WIDE = 1440;
const NARROW = 800;

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

describe("authorized companion handle", () => {
  it("mostra o handle quando /me/apps inclui delia fora da full-page e o viewport cabe o split", () => {
    assert.equal(findAuthorizedDeliaApp([helpdeskApp(), deliaApp()])?.id, "delia");
    assert.equal(
      shouldRenderCompanionHandle({
        apps: [deliaApp()],
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
      }),
      true,
    );
  });

  it("omite o handle sem id=delia mesmo com permissions e isSuperadmin fictícios", () => {
    const apps = [helpdeskApp()];
    assert.equal(findAuthorizedDeliaApp(apps), null);
    assert.equal(
      shouldRenderCompanionHandle({
        apps,
        pathname: "/",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
      }),
      false,
    );
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: true,
      }),
      false,
    );
  });

  it("omite o handle quando o workspace não comporta o split mínimo", () => {
    assert.equal(
      shouldRenderCompanionHandle({
        apps: [deliaApp()],
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: 700,
      }),
      false,
    );
    assert.equal(
      shouldRenderCompanionHandle({
        apps: [deliaApp()],
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: 800,
      }),
      true,
    );
  });

  it("omite o handle em viewport estreito sem cair para modal", () => {
    assert.equal(
      shouldRenderCompanionHandle({
        apps: [deliaApp()],
        pathname: "/apps/my-requests",
        viewportWidth: NARROW,
        workspaceWidth: NARROW,
      }),
      false,
    );
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps: [deliaApp()],
        pathname: "/apps/my-requests",
        viewportWidth: NARROW,
        workspaceWidth: NARROW,
        requestedOpen: true,
      }),
      false,
    );
  });
});

describe("full-page exclusivity", () => {
  it("esconde handle e dock na rota full-page e filhos", () => {
    assert.equal(isDeliaFullPagePath("/apps/delia", "/apps/delia"), true);
    assert.equal(isDeliaFullPagePath("/apps/delia/inbox", "/apps/delia"), true);
    assert.equal(isDeliaFullPagePath("/apps/helpdesk", "/apps/delia"), false);
    assert.equal(
      shouldRenderCompanionHandle({
        apps: [deliaApp()],
        pathname: "/apps/delia",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
      }),
      false,
    );
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps: [deliaApp()],
        pathname: "/apps/delia",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: true,
      }),
      false,
    );
  });
});

describe("dock open close and route persistence", () => {
  it("mantém o dock aberto ao trocar de rota fora da DÉLIA", () => {
    const apps = [deliaApp()];
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: true,
      }),
      true,
    );
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/apps/commercial",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: true,
      }),
      true,
    );
  });

  it("fecha sem mudar a regra de rota e devolve o handle", () => {
    const apps = [deliaApp()];
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: false,
      }),
      false,
    );
    assert.equal(
      shouldRenderCompanionHandle({
        apps,
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
      }),
      true,
    );
  });

  it("fecha o dock pedido quando a rota passa a ser a DÉLIA full-page", () => {
    const apps = [deliaApp()];
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/apps/my-requests",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
        requestedOpen: true,
      }),
      true,
    );
    assert.equal(
      shouldKeepCompanionDockOpen({
        apps,
        pathname: "/apps/delia",
        viewportWidth: WIDE,
        workspaceWidth: WIDE,
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

describe("resize bounds", () => {
  it("clampa abaixo do mínimo, dentro da faixa e acima do máximo dinâmico", () => {
    assert.equal(DELIA_DOCK_DEFAULT_WIDTH, 440);
    assert.equal(clampDeliaDockWidth(200, 1600), DELIA_DOCK_MIN_WIDTH);
    assert.equal(clampDeliaDockWidth(440, 1600), 440);
    assert.equal(clampDeliaDockWidth(900, 1600), DELIA_DOCK_MAX_WIDTH);
    assert.equal(resolveDeliaDockMaxWidth(1000), 450);
    assert.equal(clampDeliaDockWidth(500, 1000), 450);
  });

  it("ajusta pelo teclado sem sair dos limites", () => {
    assert.equal(adjustDeliaDockWidth(440, 1600, "ArrowLeft"), 464);
    assert.equal(adjustDeliaDockWidth(440, 1600, "ArrowRight"), 416);
    assert.equal(adjustDeliaDockWidth(DELIA_DOCK_MIN_WIDTH, 1600, "ArrowRight"), DELIA_DOCK_MIN_WIDTH);
    assert.equal(adjustDeliaDockWidth(DELIA_DOCK_MAX_WIDTH, 1600, "ArrowLeft"), DELIA_DOCK_MAX_WIDTH);
    assert.equal(adjustDeliaDockWidth(500, 1600, "Home"), DELIA_DOCK_MIN_WIDTH);
    assert.equal(adjustDeliaDockWidth(400, 1600, "End"), DELIA_DOCK_MAX_WIDTH);
    assert.equal(adjustDeliaDockWidth(440, 1600, "Escape"), 440);
  });
});

function fakeTarget(options: {
  connected?: boolean;
  rects?: number;
  label: string;
}): HTMLElement {
  return {
    isConnected: options.connected !== false,
    getClientRects: () => Array.from({ length: options.rects ?? 1 }),
    focus() {},
  } as unknown as HTMLElement;
}

describe("focus return", () => {
  it("devolve o foco ao handle visível", () => {
    const handle = fakeTarget({ label: "handle" });
    assert.equal(resolveFocusReturnTarget(handle, []), handle);
  });

  it("ignora handle desconectado ou sem retângulo", () => {
    const gone = fakeTarget({ label: "gone", connected: false });
    const hidden = fakeTarget({ label: "hidden", rects: 0 });
    const fallback = fakeTarget({ label: "fallback" });
    assert.equal(resolveFocusReturnTarget(gone, [fallback]), fallback);
    assert.equal(resolveFocusReturnTarget(hidden, [fallback]), fallback);
    assert.equal(resolveFocusReturnTarget(gone, [hidden]), null);
  });
});
