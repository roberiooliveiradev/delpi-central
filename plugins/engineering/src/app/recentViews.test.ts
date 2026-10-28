import { beforeEach, describe, expect, it } from "vitest";

import {
  pushRecentView,
  readRecentViews,
  resetRecentsStore,
  setRecentsIdentity,
} from "./recentViews";

class MemoryStorage {
  private map = new Map<string, string>();
  getItem(key: string) {
    return this.map.get(key) ?? null;
  }
  setItem(key: string, value: string) {
    this.map.set(key, value);
  }
}

beforeEach(() => {
  resetRecentsStore();
  (globalThis as { window?: unknown }).window = {
    localStorage: new MemoryStorage(),
  } as unknown as Window & typeof globalThis;
});

describe("recentViews", () => {
  it("guarda no máximo 5, mais recente primeiro, sem duplicar", () => {
    setRecentsIdentity("user-a");
    for (let i = 0; i < 7; i += 1) {
      pushRecentView({ routeId: `r-${i}`, label: `Rota ${i}` });
    }
    pushRecentView({ routeId: "r-6", label: "Rota 6" });
    const items = readRecentViews();
    expect(items).toHaveLength(5);
    expect(items[0].routeId).toBe("r-6");
    expect(
      items.filter((item) => item.routeId === "r-6"),
    ).toHaveLength(1);
  });

  it("escopo por identidade", () => {
    setRecentsIdentity("user-a");
    pushRecentView({ routeId: "overview", label: "Visão geral" });
    setRecentsIdentity("user-b");
    expect(readRecentViews()).toHaveLength(0);
  });

  it("leitura filtra rotas desconhecidas (acesso revogado)", () => {
    setRecentsIdentity("user-a");
    pushRecentView({ routeId: "known", label: "Conhecida" });
    pushRecentView({ routeId: "revoked", label: "Revogada" });
    const items = readRecentViews(new Set(["known"]));
    expect(items.map((i) => i.routeId)).toEqual(["known"]);
  });
});
