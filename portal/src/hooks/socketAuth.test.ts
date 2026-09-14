import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  applySocketAuthToken,
  resolveSocketAccessToken,
  shouldStartSocketConnect,
} from "./socketAuth.ts";

describe("resolveSocketAccessToken", () => {
  it("aceita token longo o bastante (positive)", () => {
    const token = "x".repeat(20);
    assert.equal(resolveSocketAccessToken(token), token);
  });

  it("aceita token com espaços nas bordas (sibling)", () => {
    const token = `  ${"y".repeat(24)}  `;
    assert.equal(resolveSocketAccessToken(token), "y".repeat(24));
  });

  it("rejeita ausente/curto (negative)", () => {
    assert.equal(resolveSocketAccessToken(undefined), null);
    assert.equal(resolveSocketAccessToken(""), null);
    assert.equal(resolveSocketAccessToken("short"), null);
  });
});

describe("shouldStartSocketConnect", () => {
  it("conecta só quando idle (positive)", () => {
    assert.equal(
      shouldStartSocketConnect({ connected: false, active: false }),
      true,
    );
  });

  it("não conecta se já conectado (sibling)", () => {
    assert.equal(
      shouldStartSocketConnect({ connected: true, active: true }),
      false,
    );
  });

  it("não conecta durante reconnect/active (negative — evita corrida)", () => {
    assert.equal(
      shouldStartSocketConnect({ connected: false, active: true }),
      false,
    );
  });
});

describe("applySocketAuthToken", () => {
  it("atualiza auth e conecta quando idle", () => {
    let connectCalls = 0;
    const socket = {
      auth: {} as Record<string, unknown>,
      connected: false,
      active: false,
      connect: () => {
        connectCalls += 1;
      },
    };

    const token = "a".repeat(32);
    assert.equal(applySocketAuthToken(socket, token), "connecting");
    assert.deepEqual(socket.auth, { token });
    assert.equal(connectCalls, 1);
  });

  it("só atualiza auth quando reconnect já está ativo", () => {
    let connectCalls = 0;
    const socket = {
      auth: {} as Record<string, unknown>,
      connected: false,
      active: true,
      connect: () => {
        connectCalls += 1;
      },
    };

    const token = "b".repeat(32);
    assert.equal(applySocketAuthToken(socket, token), "auth_updated");
    assert.deepEqual(socket.auth, { token });
    assert.equal(connectCalls, 0);
  });

  it("ignora token inválido", () => {
    let connectCalls = 0;
    const socket = {
      auth: { token: "old" } as Record<string, unknown>,
      connected: false,
      active: false,
      connect: () => {
        connectCalls += 1;
      },
    };

    assert.equal(applySocketAuthToken(socket, "x"), "skipped");
    assert.deepEqual(socket.auth, { token: "old" });
    assert.equal(connectCalls, 0);
  });
});
