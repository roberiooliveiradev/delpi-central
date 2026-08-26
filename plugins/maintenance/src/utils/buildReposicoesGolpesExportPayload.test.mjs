#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildReposicoesGolpesExportPayload } from "./buildReposicoesGolpesExportPayload.ts";

describe("buildReposicoesGolpesExportPayload", () => {
  it("monta colunas por peça e linhas por reposição", () => {
    const payload = buildReposicoesGolpesExportPayload(
      [
        {
          reposicao_id: "1",
          data_reposicao: "2026-01-10T10:00:00",
          codigo_peca: "3019001",
          golpes: 120,
          motivo_id: 1,
        },
        {
          reposicao_id: "2",
          data_reposicao: "2026-02-15T08:30:00",
          codigo_peca: "3019002",
          golpes: 80,
          motivo_id: 1,
        },
      ],
      { "3019001": "Peça A" },
    );

    assert.equal(payload.title, "Golpes por reposição");
    assert.equal(payload.columns.length, 3);
    assert.equal(payload.rows.length, 2);
    assert.equal(payload.rows[0]?.["3019001"], 120);
    assert.equal(payload.rows[0]?.["3019002"], "");
    assert.match(String(payload.columns[1]?.label), /3019001/);
  });
});
