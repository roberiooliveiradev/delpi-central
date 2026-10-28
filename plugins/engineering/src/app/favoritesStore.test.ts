import { beforeEach, describe, expect, it } from "vitest";

import {
  getFavoriteRouteIds,
  resetFavoritesStore,
  setFavoritesIdentity,
  subscribeFavorites,
  toggleFavorite,
} from "./favoritesStore";

class MemoryStorage {
  private map = new Map<string, string>();
  getItem(key: string) {
    return this.map.get(key) ?? null;
  }
  setItem(key: string, value: string) {
    this.map.set(key, value);
  }
  clear() {
    this.map.clear();
  }
}

beforeEach(() => {
  resetFavoritesStore();
  const storage = new MemoryStorage();
  (globalThis as { window?: unknown }).window = {
    localStorage: storage,
  } as unknown as Window & typeof globalThis;
});

describe("favoritesStore", () => {
  it("adiciona, remove e notifica listeners", () => {
    let notified = 0;
    const unsub = subscribeFavorites(() => {
      notified += 1;
    });
    toggleFavorite("my_requests");
    expect(getFavoriteRouteIds().has("my_requests")).toBe(true);
    toggleFavorite("my_requests");
    expect(getFavoriteRouteIds().has("my_requests")).toBe(false);
    expect(notified).toBeGreaterThanOrEqual(3);
    unsub();
  });

  it("escopo por identidade — usuários não compartilham favoritos", () => {
    setFavoritesIdentity("user-a");
    toggleFavorite("overview");
    setFavoritesIdentity("user-b");
    expect(getFavoriteRouteIds().has("overview")).toBe(false);
    toggleFavorite("help");
    setFavoritesIdentity("user-a");
    expect(getFavoriteRouteIds().has("overview")).toBe(true);
    expect(getFavoriteRouteIds().has("help")).toBe(false);
  });

  it("reset limpa cache e identidade — sem vazamento entre sessões", () => {
    setFavoritesIdentity("user-a");
    toggleFavorite("overview");
    resetFavoritesStore();
    setFavoritesIdentity("user-b");
    expect(getFavoriteRouteIds().has("overview")).toBe(false);
  });

  it("não excede o máximo de favoritos", () => {
    setFavoritesIdentity("user-a");
    for (let i = 0; i < 12; i += 1) toggleFavorite(`route-${i}`);
    expect(getFavoriteRouteIds().size).toBeLessThanOrEqual(8);
  });
});
