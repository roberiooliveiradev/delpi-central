import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ApiError } from "./api.ts";
import {
  identifyErrorMessage,
  normalizeRegistration,
  readStoredSession,
  sessionStorageKey,
  storeSession,
} from "./operatorSession.ts";

describe("operator session storage", () => {
  it("chaves a sessão por branch + workCenter", () => {
    assert.equal(
      sessionStorageKey("01", "CT-123"),
      "delpi.pcp.cockpit.bench-session.01.CT-123",
    );
    assert.notEqual(sessionStorageKey("01", "CT-123"), sessionStorageKey("02", "CT-123"));
    assert.notEqual(sessionStorageKey("01", "CT-A"), sessionStorageKey("01", "CT-B"));
  });

  it("retorna null sem sessionStorage (ambiente sem window)", () => {
    assert.equal(readStoredSession("01", "CT-123"), null);
    storeSession("01", "CT-123", null); // no-op, não lança
  });
});

describe("normalizeRegistration", () => {
  it("preserva zeros à esquerda", () => {
    assert.equal(normalizeRegistration("001"), "001");
  });

  it("faz trim e aceita texto", () => {
    assert.equal(normalizeRegistration("  20057  "), "20057");
  });

  it("rejeita vazio e acima de 30 chars", () => {
    assert.equal(normalizeRegistration(""), null);
    assert.equal(normalizeRegistration("   "), null);
    assert.equal(normalizeRegistration("1".repeat(31)), null);
    assert.equal(normalizeRegistration("1".repeat(30)), "1".repeat(30));
  });
});

describe("identifyErrorMessage", () => {
  it("mapeia 404 para matrícula não encontrada", () => {
    assert.equal(identifyErrorMessage(new ApiError("x", 404)), "Matrícula não encontrada.");
  });

  it("mapeia 403 para colaborador inativo", () => {
    assert.equal(
      identifyErrorMessage(new ApiError("x", 403)),
      "Esta matrícula não está ativa no cadastro de colaboradores.",
    );
  });

  it("mapeia 503 e erro desconhecido para indisponibilidade", () => {
    assert.match(identifyErrorMessage(new ApiError("x", 503)), /não foi possível/i);
    assert.match(identifyErrorMessage(new Error("boom")), /não foi possível/i);
  });
});
