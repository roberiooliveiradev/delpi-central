import { afterEach, describe, expect, it } from "vitest";

import {
  COMPOSER_DRAFT_TEXT_PREFIX,
  clearComposerDraftText,
  readComposerDraftText,
  writeComposerDraftText,
} from "./interactionRoomComposerDraftStorage";

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

describe("interactionRoomComposerDraftStorage", () => {
  it("persiste e limpa o markdown por sala", () => {
    (globalThis as { window?: { localStorage: typeof memoryStorage } }).window = {
      localStorage: memoryStorage,
    };
    writeComposerDraftText("room-a", "**olá**");
    expect(store.get(`${COMPOSER_DRAFT_TEXT_PREFIX}room-a`)).toMatch(/\*\*olá\*\*/);
    expect(readComposerDraftText("room-a")).toBe("**olá**");
    expect(readComposerDraftText("room-b")).toBe("");
    writeComposerDraftText("room-a", "   ");
    expect(store.has(`${COMPOSER_DRAFT_TEXT_PREFIX}room-a`)).toBe(false);
    writeComposerDraftText("room-a", "x");
    clearComposerDraftText("room-a");
    expect(readComposerDraftText("room-a")).toBe("");
  });
});
