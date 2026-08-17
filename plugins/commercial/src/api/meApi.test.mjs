import assert from "node:assert/strict";
import { describe, it } from "node:test";

function firstNameFromDisplay(name) {
  const trimmed = (name ?? "").trim();
  if (!trimmed) return null;
  return trimmed.split(/\s+/)[0] || trimmed;
}

describe("firstNameFromDisplay", () => {
  it("extrai o primeiro nome", () => {
    assert.equal(firstNameFromDisplay("João Silva Santos"), "João");
  });

  it("retorna null para vazio", () => {
    assert.equal(firstNameFromDisplay(""), null);
    assert.equal(firstNameFromDisplay(null), null);
  });
});
