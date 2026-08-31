import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isExternalHttpUrl,
  resolveManifestRouteOpenTarget,
  resolveManutencaoGeralFormUrl,
  shouldOpenManutencaoGeralInNewTab,
} from "./manutencaoGeralFormUrl.ts";

describe("manutencaoGeralFormUrl / openInNewTab", () => {
  it("reconhece Entry http(s)", () => {
    assert.equal(isExternalHttpUrl("https://script.google.com/x"), true);
    assert.equal(isExternalHttpUrl("./RemoteApp"), false);
  });

  it("resolve URL do formulário a partir do manifesto local", () => {
    const url = resolveManutencaoGeralFormUrl();
    assert.ok(url);
    assert.equal(isExternalHttpUrl(url), true);
  });

  it("marca Manutenção geral para abrir em nova aba", () => {
    assert.equal(shouldOpenManutencaoGeralInNewTab(), true);
  });

  it("resolve target openInNewTab pelo path do hub", () => {
    const target = resolveManifestRouteOpenTarget(
      "/apps/maintenance/filial-01/manutencao-geral",
      { origin: "https://portal.delpi.local" },
    );
    assert.ok(target);
    assert.equal(target.openInNewTab, true);
    assert.match(target.url, /^https:\/\/script\.google\.com\//);
  });

  it("não abre nova aba para mini-aplicadores", () => {
    assert.equal(
      resolveManifestRouteOpenTarget("/apps/maintenance/mini-aplicadores"),
      null,
    );
  });
});
