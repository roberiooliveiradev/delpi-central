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
    setHomeFavoritesLocal([{ viewId: "entry_audit" }]);
    setHomeFavoritesLocal([
      { viewId: "entry_audit" },
      { viewId: "monthly_closing" },
    ]);
    unsubscribe();
    expect(seen).toEqual(["entry_audit", "entry_audit,monthly_closing"]);
    expect(getHomeFavoritesSnapshot()).toHaveLength(2);
  });
});
