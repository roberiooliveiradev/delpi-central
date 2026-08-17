import { describe, expect, it } from "vitest";

import {
  getHomeFavoritesSnapshot,
  setHomeFavoritesLocal,
  subscribeHomeFavorites,
} from "./homeFavoritesStore";

describe("homeFavoritesStore", () => {
  it("notifica assinantes ao atualizar o cache local", () => {
    const seen: string[] = [];
    const unsubscribe = subscribeHomeFavorites((items) => {
      seen.push(items.map((item) => item.viewId).join(","));
    });
    setHomeFavoritesLocal([{ viewId: "my_day" }]);
    setHomeFavoritesLocal([
      { viewId: "my_day" },
      { viewId: "open_orders" },
    ]);
    unsubscribe();
    expect(seen).toEqual(["my_day", "my_day,open_orders"]);
    expect(getHomeFavoritesSnapshot()).toHaveLength(2);
  });
});
