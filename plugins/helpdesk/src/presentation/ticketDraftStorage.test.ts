import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearCreateDraft,
  clearReplyDraft,
  readCreateDraft,
  readReplyDraft,
  writeCreateDraft,
  writeReplyDraft,
} from "./ticketDraftStorage";

function createMemoryStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear() {
      store.clear();
    },
    getItem(key: string) {
      return store.has(key) ? store.get(key)! : null;
    },
    key(index: number) {
      return Array.from(store.keys())[index] ?? null;
    },
    removeItem(key: string) {
      store.delete(key);
    },
    setItem(key: string, value: string) {
      store.set(key, String(value));
    },
  };
}

describe("ticketDraftStorage", () => {
  beforeEach(() => {
    vi.stubGlobal("sessionStorage", createMemoryStorage());
  });

  it("preserva o rascunho de abertura e limpa quando vazio", () => {
    writeCreateDraft({
      title: "Impressora",
      description: "<p>Não imprime</p>",
      observerIdsInput: "15",
      categoryId: "3",
      urgencyId: "2",
    });
    expect(readCreateDraft()).toEqual({
      title: "Impressora",
      description: "<p>Não imprime</p>",
      observerIdsInput: "15",
      categoryId: "3",
      urgencyId: "2",
    });
    writeCreateDraft({
      title: "",
      description: "",
      observerIdsInput: "",
      categoryId: "",
      urgencyId: "",
    });
    expect(readCreateDraft()).toBeNull();
  });

  it("preserva a resposta por chamado e limpa após clear", () => {
    writeReplyDraft("42", "<p>Cabo ok</p>");
    expect(readReplyDraft("42")).toBe("<p>Cabo ok</p>");
    expect(readReplyDraft("99")).toBe("");
    clearReplyDraft("42");
    expect(readReplyDraft("42")).toBe("");
    clearCreateDraft();
  });
});
