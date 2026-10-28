#!/usr/bin/env node
/**
 * Contrato do manifesto — schemaVersion 1.0.0, id congelado,
 * permissions access/manage/access.dre (DRE-019-RW03 — legada
 * `closing-documents.read` descontinuada após migração comprovada
 * no Core) e somente as rotas implementadas.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(
  readFileSync(join(root, "controllership-finance.manifest.json"), "utf8"),
);

describe("controllership-finance manifest", () => {
  it("schemaVersion e id congelados", () => {
    assert.equal(manifest.schemaVersion, "1.0.0");
    assert.equal(manifest.id, "controllership-finance");
    assert.equal(manifest.type, "microfrontend");
    assert.equal(manifest.basePath, "/apps/controllership-finance");
    assert.equal(
      manifest.entry,
      "/apps/controllership-finance/assets/remoteEntry.js",
    );
    assert.equal(manifest.ui.renderMode, "federated");
  });

  it("permissions congeladas: access/manage/access.dre — sem legada (RW03)", () => {
    const codes = manifest.permissions.map((p) => p.code).sort();
    assert.deepEqual(codes, [
      "controllership-finance.access",
      "controllership-finance.access.dre",
      "controllership-finance.manage",
    ]);
    assert.equal(manifest.permissions.length, 3);
    for (const p of manifest.permissions) {
      assert.equal(p.module, "controllership-finance");
    }
    // RW03 — a capability legada foi removida após evidência de migração
    // no Core (papel DRE com `access.dre`, legada com zero grants). O
    // sync oficial do register_plugin remove registros ausentes — a
    // permission não pode voltar sem novo manifesto governado.
    assert.ok(
      !codes.includes("controllership-finance.closing-documents.read"),
      "capability legada reapresentada",
    );
  });

  it("somente rotas implementadas publicadas, cada uma com sua permission", () => {
    assert.equal(manifest.routes.length, 12);
    const [
      home,
      settlements,
      stockInventory,
      checklist,
      admin,
      pendencies,
      packages,
      cockpit,
      monthlyClosing,
      claraConsent,
      documents,
      dreEntry,
    ] = manifest.routes;
    assert.equal(home.path, "/apps/controllership-finance");
    assert.equal(home.permission, "controllership-finance.access");
    assert.equal(home.showInMenu, true);
    assert.equal(
      settlements.path,
      "/apps/controllership-finance/closing/financial-settlements",
    );
    assert.equal(settlements.permission, "controllership-finance.access");
    assert.equal(settlements.showInMenu, false);
    assert.equal(
      stockInventory.path,
      "/apps/controllership-finance/closing/stock-inventory",
    );
    assert.equal(stockInventory.permission, "controllership-finance.access");
    assert.equal(stockInventory.showInMenu, false);
    assert.equal(
      checklist.path,
      "/apps/controllership-finance/closing/checklist",
    );
    assert.equal(checklist.permission, "controllership-finance.access");
    assert.equal(checklist.showInMenu, false);
    assert.equal(admin.path, "/apps/controllership-finance/closing/admin");
    assert.equal(admin.permission, "controllership-finance.manage");
    assert.equal(admin.showInMenu, false);
    assert.equal(
      pendencies.path,
      "/apps/controllership-finance/closing/pendencies",
    );
    assert.equal(pendencies.permission, "controllership-finance.access");
    assert.equal(pendencies.showInMenu, false);
    assert.equal(
      packages.path,
      "/apps/controllership-finance/closing/packages",
    );
    assert.equal(packages.permission, "controllership-finance.access");
    assert.equal(packages.showInMenu, false);
    assert.equal(
      cockpit.path,
      "/apps/controllership-finance/closing/cockpit",
    );
    assert.equal(cockpit.permission, "controllership-finance.access");
    assert.equal(cockpit.showInMenu, false);
    assert.equal(
      monthlyClosing.path,
      "/apps/controllership-finance/closing/monthly-closing",
    );
    assert.equal(monthlyClosing.permission, "controllership-finance.access");
    assert.equal(monthlyClosing.showInMenu, false);
    assert.equal(
      claraConsent.path,
      "/apps/controllership-finance/closing/clara-consent",
    );
    assert.equal(claraConsent.permission, "controllership-finance.access");
    assert.equal(claraConsent.showInMenu, false);
    // DRE-019-RW02 — Documentos e interações canônico sob access.dre.
    assert.equal(
      documents.path,
      "/apps/controllership-finance/closing/documents",
    );
    assert.equal(
      documents.permission,
      "controllership-finance.access.dre",
    );
    assert.equal(documents.showInMenu, false);
    // RW04 — `/home` é a entrada visível autorizada do público DRE no
    // launcher (única rota showInMenu que ele detém); o MFE canonicaliza
    // para o basePath — não existe página «Home DRE» separada.
    assert.equal(dreEntry.path, "/apps/controllership-finance/home");
    assert.equal(dreEntry.permission, "controllership-finance.access.dre");
    assert.equal(dreEntry.showInMenu, true);
    // RW03 — a rota legada `/received-documents` foi descontinuada junto
    // com a capability antiga; o canônico é `/closing/documents`.
    for (const route of manifest.routes) {
      if (route.path.endsWith("/admin")) {
        assert.equal(route.permission, "controllership-finance.manage");
      } else if (
        route.path.endsWith("/closing/documents") ||
        route.path.endsWith("/home")
      ) {
        assert.equal(route.permission, "controllership-finance.access.dre");
      } else {
        assert.equal(route.permission, "controllership-finance.access");
      }
    }
  });

  it("nenhuma rota futura ou permission por página", () => {
    const paths = manifest.routes.map((r) => r.path);
    for (const forbidden of [
      "overview",
      "my-tasks",
      "interaction-rooms",
      "administration",
      "help",
      "closing-center",
      "received-documents",
    ]) {
      assert.ok(
        !paths.some((p) => p.includes(forbidden)),
        `rota futura publicada: ${forbidden}`,
      );
    }
    const codes = manifest.permissions.map((p) => p.code);
    for (const forbidden of [".page", ".branch", ".unit", ".indicator"]) {
      assert.ok(
        !codes.some((c) => c.includes(forbidden)),
        `permission granular proibida: ${forbidden}`,
      );
    }
  });
});
