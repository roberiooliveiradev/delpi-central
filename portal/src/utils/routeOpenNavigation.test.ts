import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isHttpUrl,
  resolveRouteOpenUrl,
} from "./routeOpenNavigation.ts";

describe("isHttpUrl", () => {
  it("aceita http e https", () => {
    assert.equal(isHttpUrl("https://script.google.com/macros/s/abc/exec"), true);
    assert.equal(isHttpUrl("http://intranet.local/app"), true);
  });

  it("rejeita relativo, vazio e esquemas não-http", () => {
    assert.equal(isHttpUrl(""), false);
    assert.equal(isHttpUrl(null), false);
    assert.equal(isHttpUrl("./RemoteApp"), false);
    assert.equal(isHttpUrl("/apps/manutencao"), false);
    assert.equal(isHttpUrl("ftp://files.local"), false);
  });
});

describe("resolveRouteOpenUrl", () => {
  const origin = "https://portal.delpi.local";

  it("usa Entry http(s) quando presente", () => {
    assert.equal(
      resolveRouteOpenUrl(
        {
          path: "/apps/manutencao/checklist",
          entry: "https://script.google.com/macros/s/abc/exec",
        },
        origin,
      ),
      "https://script.google.com/macros/s/abc/exec",
    );
  });

  it("usa origin+path quando Entry falta ou não é http", () => {
    assert.equal(
      resolveRouteOpenUrl({ path: "/apps/manutencao", entry: null }, origin),
      "https://portal.delpi.local/apps/manutencao",
    );
    assert.equal(
      resolveRouteOpenUrl(
        { path: "/apps/manutencao", entry: "./RemoteApp" },
        origin,
      ),
      "https://portal.delpi.local/apps/manutencao",
    );
  });

  it("normaliza path sem barra inicial", () => {
    assert.equal(
      resolveRouteOpenUrl({ path: "apps/foo" }, origin),
      "https://portal.delpi.local/apps/foo",
    );
  });
});
