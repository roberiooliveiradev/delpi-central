import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  readSelectedSlideId,
  resolveSelectedSlideId,
  writeSelectedSlideId,
} from "./deckSelectedSlidePreferences";

describe("deckSelectedSlidePreferences", () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("persiste e relê o slide por playlist", () => {
    writeSelectedSlideId("pl-a", "slide-2");
    expect(readSelectedSlideId("pl-a")).toBe("slide-2");
    expect(readSelectedSlideId("pl-b")).toBeNull();
  });

  it("resolve preferência salva quando o slide ainda existe", () => {
    writeSelectedSlideId("pl-1", "b");
    expect(resolveSelectedSlideId("pl-1", ["a", "b", "c"])).toBe("b");
  });

  it("cai no primeiro slide se a preferência sumiu da playlist", () => {
    writeSelectedSlideId("pl-1", "gone");
    expect(resolveSelectedSlideId("pl-1", ["a", "b"])).toBe("a");
  });

  it("remove a chave ao limpar seleção", () => {
    writeSelectedSlideId("pl-1", "a");
    writeSelectedSlideId("pl-1", null);
    expect(readSelectedSlideId("pl-1")).toBeNull();
    expect(resolveSelectedSlideId("pl-1", ["x"])).toBe("x");
  });
});
