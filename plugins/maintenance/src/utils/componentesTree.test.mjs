#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildComponentesForest, countComponenteTreeNodes } from "./componentesTree.ts";

describe("buildComponentesForest", () => {
  it("monta hierarquia por nivel", () => {
    const items = [
      { id: 1, nivel: 1, codigo: "A", descricao: "Raiz", unidade: "UN", estoque_local_01: 1, estoque_local_99: 0 },
      { id: 2, nivel: 2, codigo: "B", descricao: "Filho", unidade: "UN", estoque_local_01: 2, estoque_local_99: 0 },
      { id: 3, nivel: 2, codigo: "C", descricao: "Filho 2", unidade: "UN", estoque_local_01: 3, estoque_local_99: 0 },
      { id: 4, nivel: 1, codigo: "D", descricao: "Raiz 2", unidade: "UN", estoque_local_01: 4, estoque_local_99: 0 },
    ];

    const forest = buildComponentesForest(items);
    assert.equal(forest.length, 2);
    assert.equal(forest[0]?.item.codigo, "A");
    assert.equal(forest[0]?.children.length, 2);
    assert.equal(forest[0]?.children[0]?.item.codigo, "B");
    assert.equal(forest[1]?.item.codigo, "D");
    assert.equal(countComponenteTreeNodes(forest), 4);
  });
});
