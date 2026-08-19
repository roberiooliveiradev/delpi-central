import { afterEach, describe, expect, it } from "vitest";

import {
  INBOX_COLLAPSED_STORAGE_KEY,
  INBOX_WIDTH_STORAGE_KEY,
  readInboxCollapsed,
  readInboxWidthPx,
  writeInboxCollapsed,
  writeInboxWidthPx,
} from "./interactionRoomSplitStorage";

const store = new Map<string, string>();
const memoryStorage = {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => {
    store.set(key, value);
  },
  removeItem: (key: string) => {
    store.delete(key);
  },
};

afterEach(() => {
  store.clear();
});

describe("interactionRoomSplitStorage", () => {
  it("persists width and collapsed flag", () => {
    (globalThis as { window?: { localStorage: typeof memoryStorage } }).window = {
      localStorage: memoryStorage,
    };
    writeInboxWidthPx(320);
    writeInboxCollapsed(true);
    expect(store.get(INBOX_WIDTH_STORAGE_KEY)).toBe("320");
    expect(store.get(INBOX_COLLAPSED_STORAGE_KEY)).toBe("1");
    expect(readInboxWidthPx()).toBe(320);
    expect(readInboxCollapsed()).toBe(true);
  });
});
