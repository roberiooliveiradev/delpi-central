import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isExternalHttpUrl,
  resolveManifestRouteOpenTarget,
  resolveManutencaoGeralFormUrl,
  shouldOpenManutencaoGeralInNewTab,
  type HostAppRoute,
} from "./manutencaoGeralFormUrl.ts";

const LIVE_ENTRY = "https://script.google.com/macros/s/LIVE-FROM-PORTAL/exec";

const hostRoutes: HostAppRoute[] = [
  {
    path: "/apps/maintenance/filial-01/manutencao-geral",
    entry: LIVE_ENTRY,
    openInNewTab: true,
  },
  {
    path: "/apps/maintenance/mini-aplicadores",
    entry: null,
    openInNewTab: false,
  },
];

describe("manutencaoGeralFormUrl / manifesto vivo", () => {
  it("reconhece Entry http(s)", () => {
    assert.equal(isExternalHttpUrl("https://script.google.com/x"), true);
    assert.equal(isExternalHttpUrl("./RemoteApp"), false);
  });

  it("prioriza alternateEntry do host", () => {
    assert.equal(
      resolveManutencaoGeralFormUrl({
        alternateEntry: "https://script.google.com/macros/s/CURRENT-ROUTE/exec",
        hostRoutes,
      }),
      "https://script.google.com/macros/s/CURRENT-ROUTE/exec",
    );
  });

  it("usa Entry do manifesto vivo (appRoutes) em vez do JSON local", () => {
    assert.equal(resolveManutencaoGeralFormUrl({ hostRoutes }), LIVE_ENTRY);
  });

  it("abre nova aba com URL do manifesto vivo no hub", () => {
    const target = resolveManifestRouteOpenTarget(
      "/apps/maintenance/filial-01/manutencao-geral",
      { hostRoutes, origin: "https://portal.delpi.local" },
    );
    assert.ok(target);
    assert.equal(target.openInNewTab, true);
    assert.equal(target.url, LIVE_ENTRY);
  });

  it("honra openInNewTab do manifesto vivo", () => {
    assert.equal(shouldOpenManutencaoGeralInNewTab(hostRoutes), true);
    assert.equal(
      shouldOpenManutencaoGeralInNewTab([
        {
          path: "/apps/maintenance/filial-01/manutencao-geral",
          entry: LIVE_ENTRY,
          openInNewTab: false,
        },
      ]),
      false,
    );
  });

  it("não abre nova aba para mini-aplicadores", () => {
    assert.equal(
      resolveManifestRouteOpenTarget("/apps/maintenance/mini-aplicadores", {
        hostRoutes,
      }),
      null,
    );
  });
});
