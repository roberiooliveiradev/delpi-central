#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  isMiniAplicadoresFerramentasPath,
  resolveMaintenanceShellChrome,
  resolveMiniAplicadoresActiveId,
} from "../app/maintenanceShellChrome.ts";
import { MAINTENANCE_ROUTES } from "../constants/routes.ts";

describe("maintenanceShellChrome", () => {
  it("home não exibe TopBar", () => {
    const chrome = resolveMaintenanceShellChrome({
      view: "home",
      pathname: MAINTENANCE_ROUTES.home,
      showConfiguration: true,
    });
    assert.equal(chrome.mode, "none");
    assert.equal(chrome.showTopBar, false);
    assert.deepEqual(chrome.items, []);
  });

  it("mini-aplicadores exibe sub-abas incluindo config quando permitido", () => {
    const chrome = resolveMaintenanceShellChrome({
      view: "relatorio",
      pathname: MAINTENANCE_ROUTES.miniAplicadoresRelatorio,
      filialScope: "01",
      showConfiguration: true,
    });
    assert.equal(chrome.mode, "mini-aplicadores");
    assert.equal(chrome.showTopBar, true);
    assert.equal(chrome.activeId, "relatorio");
    assert.equal(chrome.items.length, 4);
    assert.equal(chrome.items[0]?.path, MAINTENANCE_ROUTES.filialHome("01"));
  });

  it("mini-aplicadores oculta config sem permissão", () => {
    const chrome = resolveMaintenanceShellChrome({
      view: "mini-aplicadores",
      pathname: MAINTENANCE_ROUTES.miniAplicadores,
      showConfiguration: false,
    });
    assert.equal(chrome.items.length, 3);
    assert.ok(!chrome.items.some((item) => item.id === "configuracao"));
  });

  it("detalhe ferramenta marca aba Ferramentas ativa", () => {
    const activeId = resolveMiniAplicadoresActiveId(
      "mini-aplicador",
      MAINTENANCE_ROUTES.miniAplicadorDetail("23-001"),
    );
    assert.equal(activeId, "ferramentas");
    assert.equal(
      isMiniAplicadoresFerramentasPath(MAINTENANCE_ROUTES.miniAplicadorDetail("23-001")),
      true,
    );
  });

  it("filiais usa TopBar mínima com Início", () => {
    const chrome = resolveMaintenanceShellChrome({
      view: "filiais",
      pathname: MAINTENANCE_ROUTES.filiais,
      filialScope: "02",
      showConfiguration: false,
    });
    assert.equal(chrome.mode, "submodule-back");
    assert.equal(chrome.showTopBar, true);
    assert.equal(chrome.items.length, 1);
    assert.equal(chrome.items[0]?.path, MAINTENANCE_ROUTES.filialHome("02"));
  });
});
