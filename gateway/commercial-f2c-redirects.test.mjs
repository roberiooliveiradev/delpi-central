#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = dirname(fileURLToPath(import.meta.url));
const include = "include /etc/nginx/snippets/commercial-f2c-redirects.conf;";

describe("redirects F2c do gateway", () => {
  it("ativa o snippet nos gateways canônicos", () => {
    for (const config of ["nginx.conf", "nginx.dev.conf"]) {
      assert.match(readFileSync(join(root, config), "utf8"), new RegExp(include.replaceAll(".", "\\.")));
    }
  });

  it("mantém os redirects das entradas legadas", () => {
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
