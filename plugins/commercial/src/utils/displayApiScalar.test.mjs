#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { displayApiScalar } from "./displayApiScalar.ts";

describe("displayApiScalar", () => {
  it("aceita string, boolean, number e null sem chamar .trim em não-string", () => {
    assert.equal(displayApiScalar("  SIM  "), "SIM");
    assert.equal(displayApiScalar("NAO"), "NAO");
    assert.equal(displayApiScalar(true), "Sim");
    assert.equal(displayApiScalar(false), "Não");
    assert.equal(displayApiScalar(3), "3");
    assert.equal(displayApiScalar(null), "—");
    assert.equal(displayApiScalar(undefined), "—");
    assert.equal(displayApiScalar(""), "—");
  });
});
