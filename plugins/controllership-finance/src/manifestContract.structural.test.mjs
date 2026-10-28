#!/usr/bin/env node
/**
 * Contrato do manifesto — schemaVersion 1.0.0, id congelado,
 * permissions access/manage + capability de destinatário (DRE-019)
 * e somente as rotas implementadas.
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

  it("permissions congeladas: access/manage + access.dre + legada em migração", () => {
    const codes = manifest.permissions.map((p) => p.code).sort();
    assert.deepEqual(codes, [
      "controllership-finance.access",
      "controllership-finance.access.dre",
      "controllership-finance.closing-documents.read",
      "controllership-finance.manage",
    ]);
    assert.equal(manifest.permissions.length, 4);
    for (const p of manifest.permissions) {
      assert.equal(p.module, "controllership-finance");
    }
    // RW02 — a legada permanece declarada (marcada DEPRECATED) até a
    // homologação do papel DRE; removê-la aqui quebraria destinatários
    // provisionados antes da remoção governada.
    const legacy = manifest.permissions.find(
      (p) => p.code === "controllership-finance.closing-documents.read",
    );
    assert.match(legacy.description, /DEPRECATED/);
  });

  it("somente rotas implementadas publicadas, cada uma com sua permission", () => {
    assert.equal(manifest.routes.length, 13);
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
      dreHome,
      receivedDocuments,
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
    // Home DRE — ponto de entrada visível do público externo; a correção
    // RW01 do Portal a escolhe como primeira rota visível autorizada.
    assert.equal(dreHome.path, "/apps/controllership-finance/home");
    assert.equal(dreHome.permission, "controllership-finance.access.dre");
    assert.equal(dreHome.showInMenu, true);
    // Compat transitória: mesma experiência para a capability legada até
    // a migração governada do papel DRE (remover junto com a permission).
    assert.equal(
      receivedDocuments.path,
      "/apps/controllership-finance/received-documents",
    );
    assert.equal(
      receivedDocuments.permission,
      "controllership-finance.closing-documents.read",
    );
    assert.equal(receivedDocuments.showInMenu, false);
    for (const route of manifest.routes) {
      if (route.path.endsWith("/admin")) {
        assert.equal(route.permission, "controllership-finance.manage");
      } else if (
        route.path.endsWith("/closing/documents") ||
        route.path.endsWith("/home")
      ) {
        assert.equal(route.permission, "controllership-finance.access.dre");
      } else if (route.path.endsWith("/received-documents")) {
        assert.equal(
          route.permission,
          "controllership-finance.closing-documents.read",
        );
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
