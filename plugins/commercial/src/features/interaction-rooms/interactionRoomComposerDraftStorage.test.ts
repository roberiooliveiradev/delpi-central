import { afterEach, describe, expect, it } from "vitest";

import {
  COMPOSER_DRAFT_TEXT_PREFIX,
  clearComposerDraftText,
  readComposerDraftText,
  writeComposerDraftText,
  type ComposerDraftPendingFile,
  type ComposerDraftStoredFile,
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

  it("armazena role clip e inline no payload IDB", () => {
    const clip: ComposerDraftPendingFile = {
      id: "c1",
      file: new File([new Uint8Array([1])], "a.pdf", { type: "application/pdf" }),
      role: "clip",
    };
    const inline: ComposerDraftPendingFile = {
      id: "i1",
      file: new File([new Uint8Array([2])], "b.png", { type: "image/png" }),
      role: "inline",
    };
    const payload: ComposerDraftStoredFile[] = [
      {
        id: clip.id,
        name: clip.file.name,
        type: clip.file.type,
        lastModified: clip.file.lastModified,
        buffer: new Uint8Array([1]).buffer,
        role: "clip",
      },
      {
        id: inline.id,
        name: inline.file.name,
        type: inline.file.type,
        lastModified: inline.file.lastModified,
        buffer: new Uint8Array([2]).buffer,
        role: "inline",
      },
    ];
    expect(payload.map((row) => row.role)).toEqual(["clip", "inline"]);
  });
});
