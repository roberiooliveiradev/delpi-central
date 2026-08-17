import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  clampTableFontSize,
  DEFAULT_TABLE_FONT_SIZE,
  loadTableFontSize,
  MAX_TABLE_FONT_SIZE,
  MIN_TABLE_FONT_SIZE,
  saveTableFontSize,
} from "./tableFontSizePreferences";

describe("tableFontSizePreferences", () => {
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("faz clamp entre MIN e MAX", () => {
    expect(clampTableFontSize(MIN_TABLE_FONT_SIZE - 5)).toBe(MIN_TABLE_FONT_SIZE);
    expect(clampTableFontSize(MAX_TABLE_FONT_SIZE + 5)).toBe(MAX_TABLE_FONT_SIZE);
    expect(clampTableFontSize(13.6)).toBe(14);
  });

  it("carrega default quando vazio e migra legacyStorageKeys", () => {
    expect(loadTableFontSize({ storageKey: "a:v1" })).toBe(DEFAULT_TABLE_FONT_SIZE);

    storage.set("legacy:v1", "15");
    expect(
      loadTableFontSize({
        storageKey: "a:v1",
        legacyStorageKeys: ["legacy:v1"],
      }),
    ).toBe(15);

    saveTableFontSize(12, { storageKey: "a:v1" });
    expect(storage.get("a:v1")).toBe("12");
    expect(loadTableFontSize({ storageKey: "a:v1" })).toBe(12);
  });
});
