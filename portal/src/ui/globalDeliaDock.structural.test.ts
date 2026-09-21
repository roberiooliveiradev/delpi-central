import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

function read(rel: string) {
  return readFileSync(path.join(here, rel), "utf8");
}

describe("companion dock wiring", () => {
  it("reusa o host federado do AppHost sem segundo loader", () => {
    const appHost = read("AppHost.tsx");
    const remoteHost = read("federatedRemoteHost.ts");
    const dockLogic = read("globalDeliaDock.ts");
    const dock = read("GlobalDeliaDock.tsx");
    const hook = read("useFederatedRemoteMount.ts");
    const app = read("App.tsx");

    assert.match(appHost, /loadFederatedExposedModule/);
    assert.match(appHost, /updateFederatedRemote/);
    assert.match(appHost, /unmountFederatedRemote/);
    assert.doesNotMatch(appHost, /loadFederatedContainer/);
    assert.match(remoteHost, /ownGeneration !== generation/);
    assert.match(dockLogic, /DELIA_APP_ID = "delia"/);
    assert.match(dockLogic, /DELIA_EXPOSED_MODULE = "\.\/App"/);
    assert.doesNotMatch(dockLogic, /permissions\.includes/);
    assert.match(dockLogic, /Do not consult permissions, roles, groups, or isSuperadmin/);
    assert.match(dock, /useFederatedRemoteMount/);
    assert.match(dock, /reclampDeliaDockWidth/);
    assert.match(dock, /aria-label="DÉLIA"/);
    assert.match(dock, /aria-label="Abrir DÉLIA ao lado"/);
    assert.match(dock, /aria-label="Abrir página completa"/);
    assert.match(dock, /role="separator"/);
    assert.match(hook, /\[options\.enabled, options\.entryUrl, options\.exposedModule, options\.props\.getAccessToken\]/);
    assert.doesNotMatch(dock, /localStorage|sessionStorage|indexedDB/i);
    assert.doesNotMatch(dockLogic, /localStorage|sessionStorage|indexedDB/i);
    assert.match(app, /GlobalDeliaDockProvider/);
    assert.match(app, /<AppHost /);
    assert.doesNotMatch(app, /GlobalDeliaProvider/);
  });

  it("não cria permissão, catálogo paralelo ou contrato de host novo", () => {
    const dockLogic = read("globalDeliaDock.ts");
    const dock = read("GlobalDeliaDock.tsx");
    assert.doesNotMatch(dockLogic, /delia\.global|delia\.panel|delia\.assistant/);
    assert.doesNotMatch(dock, /delia\.global|delia\.panel/);
    assert.doesNotMatch(dockLogic, /WorkspaceContext|EntityRef|SourceRef|surface:|mode:/);
    assert.doesNotMatch(dock, /WorkspaceContext|EntityRef|SourceRef/);
    assert.doesNotMatch(dock, /surface="dock"|mode="companion"/);
  });

  it("remove o launcher especial da sidebar e da barra mobile", () => {
    const sidebar = read("../layout/Sidebar.tsx");
    const mobile = read("../layout/PortalMobileNavBar.tsx");
    assert.doesNotMatch(sidebar, /GlobalDeliaSidebarLauncher/);
    assert.doesNotMatch(mobile, /GlobalDeliaMobileLauncher/);
    assert.match(sidebar, /SidebarFavoritesList/);
    assert.match(sidebar, /AppLauncher/);
  });

  it("não conserva semântica de modal nem fecha ao interagir com o app central", () => {
    const dock = read("GlobalDeliaDock.tsx");
    const css = read("GlobalDeliaDock.css");
    const logic = read("globalDeliaDock.ts");
    assert.doesNotMatch(dock, /createPortal/);
    assert.doesNotMatch(dock, /aria-modal/);
    assert.doesNotMatch(dock, /role="dialog"/);
    assert.doesNotMatch(dock, /global-delia-backdrop/);
    assert.doesNotMatch(css, /global-delia-backdrop/);
    assert.doesNotMatch(dock, /document\.body\.style\.overflow/);
    assert.doesNotMatch(dock, /addEventListener\(\s*["']keydown["']/);
    assert.doesNotMatch(dock, /listModalFocusables|resolveModalTabTarget/);
    assert.doesNotMatch(logic, /listModalFocusables|resolveModalTabTarget/);
    assert.doesNotMatch(dock, /onClick=\{close\}/);
    assert.match(dock, /<aside/);
  });
});
