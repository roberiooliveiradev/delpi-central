#!/usr/bin/env node
/**
 * Validação do manifesto local (Etapa 6) — node:test, sem deps novas.
 * Espelha regras canônicas de PATH_RE / SemVer da Core API (manifest_rules.py).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pluginRoot = join(__dirname, "..");
const PREVIOUS_VERSION = "1.1.0";
const EXPECTED_VERSION = "1.2.0";

const SEMVER_RE = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const PATH_RE = /^\/[-a-z0-9/]*$/;

function loadManifest() {
  return JSON.parse(
    readFileSync(join(pluginRoot, "pedidos-venda-abertos.manifest.json"), "utf8"),
  );
}

describe("pedidos-venda-abertos.manifest.json (Etapa 6)", () => {
  const manifest = loadManifest();
  const pkg = JSON.parse(readFileSync(join(pluginRoot, "package.json"), "utf8"));

  it("preserva plugin id e basePath", () => {
    assert.equal(manifest.id, "pedidos-venda-abertos");
    assert.equal(manifest.basePath, "/apps/pedidos-venda-abertos");
    assert.equal(manifest.type, "microfrontend");
    assert.equal(manifest.entry, "/apps/pedidos-venda-abertos/assets/remoteEntry.js");
  });

  it("nova versao SemVer valida e diferente da anterior", () => {
    assert.match(manifest.version, SEMVER_RE);
    assert.equal(manifest.version, EXPECTED_VERSION);
    assert.notEqual(manifest.version, PREVIOUS_VERSION);
    assert.equal(pkg.version, manifest.version);
  });

  it("schemaVersion e permissoes .access + .admin", () => {
    assert.equal(manifest.schemaVersion, "1.0.0");
    const codes = (manifest.permissions || []).map((p) => p.code);
    assert.deepEqual(codes, [
      "pedidos-venda-abertos.access",
      "pedidos-venda-abertos.admin",
    ]);
    assert.equal(manifest.permissions[0].module, "pedidos-venda-abertos");
  });

  it("nome exibido coerente com Portal do Vendedor", () => {
    assert.equal(manifest.name, "Portal do Vendedor");
    assert.match(manifest.description, /Portal comercial/i);
    assert.doesNotMatch(JSON.stringify(manifest), /fornecedor|SA2|SC7|compras/i);
  });

  it("rota principal visivel unica no menu", () => {
    const visible = (manifest.routes || []).filter((r) => r.showInMenu !== false);
    assert.equal(visible.length, 1);
    assert.equal(visible[0].path, "/apps/pedidos-venda-abertos");
    assert.equal(visible[0].label, "Portal do Vendedor");
    assert.equal(visible[0].permission, "pedidos-venda-abertos.access");
  });

  it("rota de Clientes e Configuracao ocultas", () => {
    const clientes = (manifest.routes || []).find(
      (r) => r.path === "/apps/pedidos-venda-abertos/clientes",
    );
    assert.ok(clientes);
    assert.equal(clientes.showInMenu, false);
    assert.equal(clientes.permission, "pedidos-venda-abertos.access");
    assert.equal(clientes.label, "Minha carteira");

    const config = (manifest.routes || []).find(
      (r) => r.path === "/apps/pedidos-venda-abertos/configuracao",
    );
    assert.ok(config);
    assert.equal(config.showInMenu, false);
    assert.equal(config.permission, "pedidos-venda-abertos.admin");
  });

  it("todas as rotas iniciam pelo basePath e PATH_RE", () => {
    const paths = new Set();
    for (const route of manifest.routes || []) {
      assert.ok(route.path.startsWith(manifest.basePath));
      assert.match(route.path, PATH_RE);
      assert.ok(!paths.has(route.path), `path duplicado: ${route.path}`);
      paths.add(route.path);
    }
  });

  it("nao declara rota dinamica com parametros (PATH_RE nao permite)", () => {
    const joined = (manifest.routes || []).map((r) => r.path).join("\n");
    assert.doesNotMatch(joined, /:codigo|:loja|\*|\(/);
    assert.equal(
      PATH_RE.test("/apps/pedidos-venda-abertos/clientes/:codigo/:loja"),
      false,
    );
  });

  it("ui.renderMode federated e icone preservado", () => {
    assert.equal(manifest.ui?.renderMode, "federated");
    assert.equal(manifest.icon, "clipboard-list");
  });
});
