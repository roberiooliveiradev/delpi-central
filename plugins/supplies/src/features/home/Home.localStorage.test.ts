import { beforeEach, describe, expect, it } from "vitest";

import {
  loadHomeFavoritesFromStorage,
  resetHomeFavoritesStoreForTests,
  toggleHomeFavorite,
} from "../../app/homeFavoritesStore";
import {
  filterFavoritesByCaps,
  readFavorites,
  toggleFavorite,
} from "./homeFavorites";
import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
} from "./homeRecentViews";

const allCaps = {
  analytics: true,
  purchaseRequests: true,
  operations: true,
  administration: true,
};

function installStorageMock() {
  const store = new Map<string, string>();
  (globalThis as { window?: unknown }).window = {
    localStorage: {
      getItem(key: string) {
        return store.has(key) ? store.get(key)! : null;
      },
      setItem(key: string, value: string) {
        store.set(key, String(value));
      },
      clear() {
        store.clear();
      },
    },
  };
}

describe("home localStorage", () => {
  beforeEach(() => {
    installStorageMock();
    resetHomeFavoritesStoreForTests();
  });

  it("stores and filters recents by capability", () => {
    pushRecentView({ viewId: "overview", label: "Visão geral" });
    pushRecentView({ viewId: "help", label: "Ajuda" });
    expect(readRecentViews()).toHaveLength(2);
    const filtered = filterRecentsByCaps(readRecentViews(), {
      ...allCaps,
      analytics: false,
    });
    expect(filtered.map((item) => item.viewId)).toEqual(["help"]);
  });

  it("toggles favorites and filters by capability", () => {
    toggleFavorite({ viewId: "purchase_orders", label: "Pedidos" });
    toggleFavorite({ viewId: "my_tasks", label: "Tarefas" });
    expect(readFavorites()).toHaveLength(2);
    toggleFavorite({ viewId: "purchase_orders", label: "Pedidos" });
    expect(readFavorites().map((item) => item.viewId)).toEqual(["my_tasks"]);
    const filtered = filterFavoritesByCaps(readFavorites(), {
      ...allCaps,
      operations: false,
    });
    expect(filtered.map((item) => item.viewId)).toEqual(["my_tasks"]);
  });

  it("sincroniza store com localStorage para a TopBar", () => {
    loadHomeFavoritesFromStorage();
    toggleHomeFavorite({ viewId: "overview", label: "Visão geral" });
    expect(readFavorites().map((item) => item.viewId)).toEqual(["overview"]);
    toggleHomeFavorite({ viewId: "overview", label: "Visão geral" });
    expect(readFavorites()).toHaveLength(0);
  });
});
