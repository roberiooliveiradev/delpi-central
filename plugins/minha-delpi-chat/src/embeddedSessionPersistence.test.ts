import { describe, expect, it, beforeEach } from "vitest";

import {
  buildEmbeddedSessionScopeKey,
  clearEmbeddedSessionId,
  readEmbeddedSessionId,
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
