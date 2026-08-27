import { afterEach, describe, expect, it } from "vitest";

import { createDefaultUrlState } from "./urlState";
import {
  SAVED_FILTERS_STORAGE_KEY,
  applySavedFilters,
  areSavedFiltersEqual,
  loadSavedFilters,
  persistSavedFilters,
  resolveInitialUrlState,
  snapshotSavedFilters,
} from "./savedFilters";

const memory = new Map<string, string>();

const storage = {
  getItem: (key: string) => memory.get(key) ?? null,
  setItem: (key: string, value: string) => {
    memory.set(key, value);
  },
  removeItem: (key: string) => {
    memory.delete(key);
  },
};

function installStorage() {
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: { localStorage: storage },
  });
}

afterEach(() => {
  memory.clear();
  Reflect.deleteProperty(globalThis, "window");
});

describe("savedFilters", () => {
  it("persists and restores filters without page or request", () => {
    installStorage();
    const snapshot = persistSavedFilters({
      branch: "02",
      date_from: "2026-08-01",
      date_to: "2026-08-31",
      request_number: "177030",
      requester_user_ids: ["USR01"],
      cost_center_codes: ["0413", "0520"],
      product_code: "",
      supplier_code: "",
      order_number: "",
      overall_stages: ["awaiting_order", "awaiting_receipt"],
      page: 4,
      page_size: 25,
    });
    expect("page" in snapshot).toBe(false);
    expect(JSON.parse(memory.get(SAVED_FILTERS_STORAGE_KEY) ?? "{}").overall_stages).toEqual([
      "awaiting_order",
      "awaiting_receipt",
    ]);
    expect(loadSavedFilters()).toEqual(snapshot);
  });

  it("applies saved filters on empty URL before first fetch", () => {
    installStorage();
    persistSavedFilters({
      ...createDefaultUrlState("01"),
      overall_stages: ["awaiting_order"],
      cost_center_codes: ["0413"],
    });
    const state = resolveInitialUrlState("", "01");
    expect(state.overall_stages).toEqual(["awaiting_order"]);
    expect(state.cost_center_codes).toEqual(["0413"]);
    expect(state.page).toBe(1);
    expect(state.request).toBe("");
  });

  it("keeps deep-link URL over saved filters", () => {
    installStorage();
    persistSavedFilters({
      ...createDefaultUrlState("01"),
      overall_stages: ["completed"],
    });
    const state = resolveInitialUrlState("?request=02:164708&branch=02", "01");
    expect(state.request).toBe("02:164708");
    expect(state.branch).toBe("02");
    expect(state.overall_stages).toEqual([]);
  });

  it("does not overwrite request when applying saved snapshot", () => {
    const base = { ...createDefaultUrlState("01"), request: "01:1" };
    const next = applySavedFilters(base, snapshotSavedFilters({
      ...base,
      overall_stages: ["awaiting_receipt"],
    }));
    expect(next.request).toBe("01:1");
    expect(next.overall_stages).toEqual(["awaiting_receipt"]);
    expect(areSavedFiltersEqual(snapshotSavedFilters(next), snapshotSavedFilters(next))).toBe(true);
  });
});
