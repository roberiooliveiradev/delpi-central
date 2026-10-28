#!/usr/bin/env node
/**
 * Regressão: fetch da página não pode depender da identidade de `filters.apiParams`
 * (objeto recriado a cada render → loop de loading/abort).
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const pagePath = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "BillingByCustomerMonthPage.tsx",
);

describe("BillingByCustomerMonthPage fetch deps", () => {
  it("não usa filters.apiParams como dependência do efeito de carga", async () => {
    const source = await readFile(pagePath, "utf8");
    assert.equal(
      /},\s*\[\s*filters\.apiParams\b/.test(source),
      false,
      "useEffect de fetch não deve listar filters.apiParams (identidade instável)",
    );
    assert.match(
      source,
      /period\.start,\s*\n\s*period\.end,\s*\n\s*billingNature,\s*\n\s*reloadKey/,
      "deps devem incluir período/natureza/reload como primitivos",
    );
  });
});
