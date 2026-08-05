import { describe, expect, it, beforeEach } from "vitest";

import {
  buildEmbeddedSessionScopeKey,
  clearEmbeddedSessionId,
  readEmbeddedSessionId,
  resolveEmbeddedSessionRestore,
  writeEmbeddedSessionId,
} from "./embeddedSessionPersistence";

describe("embeddedSessionPersistence", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    const storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    };
    (globalThis as { window?: unknown }).window = {
      localStorage: storage,
    };
  });

  it("monta chave por surface e playlist", () => {
    expect(
      buildEmbeddedSessionScopeKey({
        surface: "tv-dashboard",
        playlistId: "pl-1",
      }),
    ).toBe("tv-dashboard:pl-1");
    expect(
      buildEmbeddedSessionScopeKey({
        surface: null,
        playlistId: null,
      }),
    ).toBe("tv-dashboard:_default");
  });

  it("persiste e lê sessionId por escopo", () => {
    const scope = buildEmbeddedSessionScopeKey({
      surface: "tv-dashboard",
      playlistId: "pl-9",
    });
    expect(readEmbeddedSessionId(scope)).toBeNull();
    writeEmbeddedSessionId(scope, "sess-abc");
    expect(readEmbeddedSessionId(scope)).toBe("sess-abc");
    clearEmbeddedSessionId(scope);
    expect(readEmbeddedSessionId(scope)).toBeNull();
  });
});

describe("resolveEmbeddedSessionRestore", () => {
  it("espera a lista antes de descartar a sessão guardada", () => {
    // Regressão: criar slide remontava o painel e a lista chegava depois;
    // descartar aqui abria conversa nova e o histórico do turno desaparecia.
    expect(
      resolveEmbeddedSessionRestore({
        storedId: "sess-1",
        sessionIds: [],
        isLoadingSessions: false,
      }),
    ).toEqual({ action: "wait" });

    expect(
      resolveEmbeddedSessionRestore({
        storedId: "sess-1",
        sessionIds: [],
        isLoadingSessions: true,
      }),
    ).toEqual({ action: "wait" });
  });

  it("restaura a sessão guardada quando ela está na lista", () => {
    expect(
      resolveEmbeddedSessionRestore({
        storedId: "sess-1",
        sessionIds: ["sess-0", "sess-1"],
        isLoadingSessions: false,
      }),
    ).toEqual({ action: "restore", sessionId: "sess-1" });
  });

  it("descarta somente quando a sessão não existe mais no servidor", () => {
    expect(
      resolveEmbeddedSessionRestore({
        storedId: "sess-apagada",
        sessionIds: ["sess-0"],
        isLoadingSessions: false,
      }),
    ).toEqual({ action: "discard" });
  });

  it("persiste a sessão ativa em vez de restaurar", () => {
    expect(
      resolveEmbeddedSessionRestore({
        storedId: "sess-1",
        sessionIds: ["sess-1"],
        isLoadingSessions: false,
        activeSessionId: "sess-2",
      }),
    ).toEqual({ action: "persist", sessionId: "sess-2" });
  });
});
