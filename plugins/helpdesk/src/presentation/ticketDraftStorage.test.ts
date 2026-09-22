import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  assigneeFromCreateDraft,
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
      assigneeId: "22",
      assigneeName: "Ana Silva",
      assigneeEmail: "ana@delpi.com.br",
      assigneeDirectoryUserId: "delpi-ana",
      assigneeHasPhoto: true,
      categoryId: "3",
      urgencyId: "2",
    });
    expect(readCreateDraft()).toEqual({
      title: "Impressora",
      description: "<p>Não imprime</p>",
      observerIdsInput: "15",
      assigneeId: "22",
      assigneeName: "Ana Silva",
      assigneeEmail: "ana@delpi.com.br",
      assigneeDirectoryUserId: "delpi-ana",
      assigneeHasPhoto: true,
      categoryId: "3",
      urgencyId: "2",
    });
    expect(assigneeFromCreateDraft(readCreateDraft())).toEqual({
      id: "22",
      name: "Ana Silva",
      email: "ana@delpi.com.br",
      directoryUserId: "delpi-ana",
      hasPhoto: true,
    });
    writeCreateDraft({
      title: "",
      description: "",
      observerIdsInput: "",
      assigneeId: "",
      assigneeName: "",
      assigneeEmail: "",
      assigneeDirectoryUserId: "",
      assigneeHasPhoto: false,
      categoryId: "",
      urgencyId: "",
    });
    expect(readCreateDraft()).toBeNull();
  });

  it("F5 legado: só assigneeId vira snapshot Usuário {id}", () => {
    sessionStorage.setItem(
      "helpdesk:ticket-create-draft:v1",
      JSON.stringify({
        title: "x",
        description: "",
        observerIdsInput: "",
        assigneeId: "11",
        categoryId: "",
        urgencyId: "",
      }),
    );
    const draft = readCreateDraft();
    expect(draft?.assigneeId).toBe("11");
    expect(assigneeFromCreateDraft(draft)).toEqual({
      id: "11",
      name: "Usuário 11",
      email: "",
      directoryUserId: undefined,
      hasPhoto: false,
    });
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
