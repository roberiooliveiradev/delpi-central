import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

function read(rel: string) {
  return readFileSync(path.join(here, rel), "utf8");
}

describe("global DÉLIA surface wiring", () => {
  it("reusa o host federado do AppHost sem segundo loader", () => {
    const appHost = read("AppHost.tsx");
    const remoteHost = read("federatedRemoteHost.ts");
    const surface = read("globalDeliaSurface.ts");
    const panel = read("GlobalDeliaSurface.tsx");
    const app = read("App.tsx");

    assert.match(appHost, /loadFederatedExposedModule/);
    assert.match(appHost, /updateFederatedRemote/);
    assert.match(appHost, /unmountFederatedRemote/);
    assert.doesNotMatch(appHost, /loadFederatedContainer/);
    assert.match(remoteHost, /ownGeneration !== generation/);
    assert.match(surface, /DELIA_APP_ID = "delia"/);
    assert.match(surface, /DELIA_EXPOSED_MODULE = "\.\/App"/);
    assert.doesNotMatch(surface, /permissions\.includes/);
    assert.match(surface, /Do not consult permissions, roles, groups, or isSuperadmin/);
    assert.match(panel, /resolveModalTabTarget/);
    assert.match(panel, /resolveFocusReturnTarget/);
    assert.match(panel, /openerRef/);
    assert.match(panel, /mobileLauncherRef/);
    assert.doesNotMatch(panel, /localStorage|sessionStorage|indexedDB/i);
    assert.match(app, /GlobalDeliaProvider/);
    assert.match(app, /<AppHost /);
  });

  it("não cria permissão ou catálogo paralelo", () => {
    const surface = read("globalDeliaSurface.ts");
    const panel = read("GlobalDeliaSurface.tsx");
    assert.doesNotMatch(surface, /delia\.global|delia\.panel|delia\.assistant/);
    assert.doesNotMatch(panel, /delia\.global|delia\.panel/);
    assert.doesNotMatch(surface, /WorkspaceContext/);
    assert.doesNotMatch(panel, /WorkspaceContext|EntityRef|SourceRef/);
  });
});
