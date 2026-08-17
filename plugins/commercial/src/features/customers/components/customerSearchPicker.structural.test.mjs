#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "CustomerSearchPicker.tsx"), "utf8");

describe("CustomerSearchPicker", () => {
  it("oferece atalho para selecionar todos os resultados filtrados", () => {
    assert.match(source, /selectAllHits/);
    assert.match(source, /Selecionar todos filtrados/);
    assert.match(source, /maxSelected/);
    assert.match(source, /excludeKeys/);
    assert.match(source, /visibleHits/);
    assert.match(source, /já selecionados ou vinculados/);
  });
});
