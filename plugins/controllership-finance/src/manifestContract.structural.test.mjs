#!/usr/bin/env node
/**
 * Contrato do manifesto IMP-MFE-HOME — schemaVersion 1.0.0, id congelado,
 * somente as duas permissions e somente a rota Home implementada.
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

  it("exatamente as duas permissions congeladas — nenhuma extra", () => {
    const codes = manifest.permissions.map((p) => p.code).sort();
    assert.deepEqual(codes, [
      "controllership-finance.access",
      "controllership-finance.manage",
    ]);
    assert.equal(manifest.permissions.length, 2);
    for (const p of manifest.permissions) {
      assert.equal(p.module, "controllership-finance");
    }
  });

  it("somente rotas implementadas publicadas, protegidas por .access", () => {
    assert.equal(manifest.routes.length, 2);
    const [home, settlements] = manifest.routes;
    assert.equal(home.path, "/apps/controllership-finance");
    assert.equal(home.permission, "controllership-finance.access");
    assert.equal(home.showInMenu, true);
    assert.equal(
      settlements.path,
      "/apps/controllership-finance/closing/financial-settlements",
    );
    assert.equal(settlements.permission, "controllership-finance.access");
    assert.equal(settlements.showInMenu, false);
    for (const route of manifest.routes) {
      assert.equal(route.permission, "controllership-finance.access");
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
      "cockpit",
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
