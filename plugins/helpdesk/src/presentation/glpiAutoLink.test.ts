import { describe, expect, it } from "vitest";

import {
  HELPDESK_GLPI_AUTO_LINK_KEY,
  clearGlpiAutoLinkAttempt,
  markGlpiAutoLinkAttempted,
  shouldAutoStartGlpiLink,
} from "./glpiAutoLink";

function memoryStorage(): Storage {
  const data = new Map<string, string>();
  return {
    get length() {
      return data.size;
    },
    clear() {
      data.clear();
    },
    getItem(key: string) {
      return data.has(key) ? data.get(key)! : null;
    },
    key(index: number) {
      return [...data.keys()][index] ?? null;
    },
    removeItem(key: string) {
      data.delete(key);
    },
    setItem(key: string, value: string) {
      data.set(key, value);
    },
  };
}

describe("glpiAutoLink", () => {
  it("permite auto-start na primeira tentativa", () => {
    const storage = memoryStorage();
    expect(shouldAutoStartGlpiLink(storage)).toBe(true);
  });

  it("bloqueia auto-start após tentativa marcada (evita loop)", () => {
    const storage = memoryStorage();
    markGlpiAutoLinkAttempted(storage);
    expect(storage.getItem(HELPDESK_GLPI_AUTO_LINK_KEY)).toBe("1");
    expect(shouldAutoStartGlpiLink(storage)).toBe(false);
  });

  it("libera de novo após limpar (lista carregou com sessão)", () => {
    const storage = memoryStorage();
    markGlpiAutoLinkAttempted(storage);
    clearGlpiAutoLinkAttempt(storage);
    expect(shouldAutoStartGlpiLink(storage)).toBe(true);
  });

  it("sem storage ainda permite auto-start", () => {
    expect(shouldAutoStartGlpiLink(null)).toBe(true);
  });
});
