#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildLinearTrendValues,
  withLinearTrendField,
} from "./linearTrendSeries.ts";

describe("buildLinearTrendValues", () => {
  it("retorna nulls quando há menos de 2 pontos finitos", () => {
    assert.deepEqual(buildLinearTrendValues([]), []);
    assert.deepEqual(buildLinearTrendValues([10]), [null]);
    assert.deepEqual(buildLinearTrendValues([null, 5, null]), [null, null, null]);
  });

  it("ajusta reta y = x em série 0..n", () => {
    const values = [0, 1, 2, 3, 4];
    const trend = buildLinearTrendValues(values);
    for (let i = 0; i < values.length; i += 1) {
      assert.ok(trend[i] != null);
      assert.ok(Math.abs(Number(trend[i]) - i) < 1e-9);
    }
  });

  it("ignora nulls no fit e avalia em todos os índices", () => {
    const trend = buildLinearTrendValues([0, null, 2, null, 4]);
    assert.ok(trend[0] != null && Math.abs(Number(trend[0]) - 0) < 1e-9);
    assert.ok(trend[2] != null && Math.abs(Number(trend[2]) - 2) < 1e-9);
    assert.ok(trend[4] != null && Math.abs(Number(trend[4]) - 4) < 1e-9);
    assert.ok(trend[1] != null && Math.abs(Number(trend[1]) - 1) < 1e-9);
  });
});

describe("withLinearTrendField", () => {
  it("anexa campo de tendência sem mutar a fonte", () => {
    const rows = [
      { periodo: "a", faturamento: 10 },
      { periodo: "b", faturamento: 20 },
      { periodo: "c", faturamento: 30 },
    ];
    const out = withLinearTrendField(rows, "faturamento", "_trend");
    assert.equal(rows[0]._trend, undefined);
    assert.ok(out[0]._trend != null);
    assert.ok(Math.abs(Number(out[0]._trend) - 10) < 1e-9);
    assert.ok(Math.abs(Number(out[2]._trend) - 30) < 1e-9);
  });
});
