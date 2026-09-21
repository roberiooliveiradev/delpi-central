import { beforeEach, describe, expect, it, vi } from "vitest";

import { lastHelpdeskListPath, rememberHelpdeskListPath } from "./listNavigationMemory";

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

describe("listNavigationMemory", () => {
  beforeEach(() => {
    vi.stubGlobal("sessionStorage", createMemoryStorage());
  });

  it("guarda o recorte da lista e devolve no Voltar", () => {
    rememberHelpdeskListPath("/apps/helpdesk?status=open&page=2&q=monitor");
    expect(lastHelpdeskListPath()).toBe("/apps/helpdesk?status=open&page=2&q=monitor");
  });

  it("ignora detalhe e formulário e cai no root da lista", () => {
    rememberHelpdeskListPath("/apps/helpdesk/tickets/42");
    expect(lastHelpdeskListPath()).toBe("/apps/helpdesk");
    rememberHelpdeskListPath("/apps/helpdesk/tickets/new");
    expect(lastHelpdeskListPath()).toBe("/apps/helpdesk");
  });

  it("normaliza barra final no path da lista", () => {
    rememberHelpdeskListPath("/apps/helpdesk/?urgency_id=3");
    expect(lastHelpdeskListPath()).toBe("/apps/helpdesk?urgency_id=3");
  });
});
