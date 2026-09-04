#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = dirname(fileURLToPath(import.meta.url));
const include =
  "include /etc/nginx/snippets/invoice-issuance-to-my-requests-redirects.conf;";

describe("redirects soft cutover invoice-issuance → my-requests (E12)", () => {
  it("inclui o snippet ativo em nginx prod e dev", () => {
    for (const config of ["nginx.conf", "nginx.dev.conf"]) {
      const text = readFileSync(join(root, config), "utf8");
      assert.match(
        text,
        new RegExp(`^\\s*${include.replaceAll(".", "\\.")}`, "m"),
        `${config} deve incluir redirects E12 ativos`,
      );
    }
  });

  it("mapeia filiais para wizard canônico e raiz para my-requests", () => {
    const snippet = readFileSync(
      join(root, "snippets", "invoice-issuance-to-my-requests-redirects.conf"),
      "utf8",
    );
    assert.match(snippet, /location = \/apps\/invoice-issuance \{/);
    assert.match(snippet, /return 302 \/apps\/my-requests;/);
    assert.match(
      snippet,
      /return 302 \/apps\/my-requests\/new\?type=invoice-issuance;/,
    );
    assert.match(snippet, /\(\?!assets\/\)/);
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
