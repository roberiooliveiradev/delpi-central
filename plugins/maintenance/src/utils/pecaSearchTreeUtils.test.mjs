#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveAutoExpandedPecaCodes } from "./pecaSearchTreeUtils.ts";

describe("resolveAutoExpandedPecaCodes", () => {
  const items = [{ codigo: "30190001" }, { codigo: "30190002" }];

  it("não expande sem filtro ativo", () => {
    assert.deepEqual(resolveAutoExpandedPecaCodes(items, {}), new Set());
    assert.deepEqual(
      resolveAutoExpandedPecaCodes(items, { codigo: "  ", descricao: "" }),
      new Set(),
    );
  });

  it("expande todas as peças visíveis após busca com código", () => {
    assert.deepEqual(
      resolveAutoExpandedPecaCodes(items, { codigo: "3019" }),
      new Set(["30190001", "30190002"]),
    );
  });

  it("expande após busca com descrição", () => {
    assert.deepEqual(
      resolveAutoExpandedPecaCodes(items, { descricao: "GRAMPEADOR" }),
      new Set(["30190001", "30190002"]),
    );
  });
});
