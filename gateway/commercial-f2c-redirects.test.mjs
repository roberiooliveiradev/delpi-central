#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = dirname(fileURLToPath(import.meta.url));
const include = "include /etc/nginx/snippets/commercial-f2c-redirects.conf;";

describe("redirects F2c do gateway", () => {
  it("mantém o snippet disponível, mas desativado até o flip do runbook", () => {
    for (const config of ["nginx.conf", "nginx.dev.conf"]) {
      const text = readFileSync(join(root, config), "utf8");
      assert.doesNotMatch(
        text,
        new RegExp(`^\\s*${include.replaceAll(".", "\\.")}`, "m"),
        `${config} não deve incluir redirects F2c ativos antes do cutover RBAC`,
      );
      assert.match(
        text,
        /commercial-f2c-redirects\.conf/,
        `${config} deve documentar o snippet comentado para o flip`,
      );
    }
  });

  it("mantém os redirects das entradas legadas no snippet", () => {
    const snippet = readFileSync(
      join(root, "snippets", "commercial-f2c-redirects.conf"),
      "utf8",
    );
    assert.match(snippet, /location = \/apps\/pedidos-venda-abertos \{/);
    assert.match(snippet, /return 302 \/apps\/commercial\/open-orders;/);
    assert.match(snippet, /return 302 \/apps\/commercial\/customers;/);
    assert.match(snippet, /return 302 \/apps\/commercial\/seller-portfolios;/);
    assert.match(
      snippet,
      /return 302 \/apps\/commercial\/customers\/\$1\/\$2;/,
    );
  });

  it("copia o diretório de snippets nas imagens dev e prod", () => {
    for (const dockerfile of ["Dockerfile.dev", "Dockerfile.prod"]) {
      assert.match(
        readFileSync(join(root, dockerfile), "utf8"),
        /COPY snippets\/ \/etc\/nginx\/snippets\//,
      );
    }
  });
});
