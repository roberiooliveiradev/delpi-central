import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
} from "./homeRecentViews.ts";

function installStorageMock() {
  const store = new Map();
  globalThis.window = {
    localStorage: {
      getItem(key) {
        return store.has(key) ? store.get(key) : null;
      },
      setItem(key, value) {
        store.set(key, String(value));
      },
      clear() {
        store.clear();
      },
    },
  };
}

describe("homeRecentViews", () => {
  it("dedupe por viewId+search e limita a 5", () => {
    installStorageMock();
    pushRecentView({ viewId: "open_orders", label: "Meus pedidos" });
    pushRecentView({
      viewId: "open_orders",
      search: "?focus=late",
      label: "Em atraso",
    });
    pushRecentView({ viewId: "open_orders", label: "Meus pedidos" });
    const items = readRecentViews();
    assert.equal(items[0]?.label, "Meus pedidos");
    assert.equal(items.length, 2);

    const extras = [
      { viewId: "overview", label: "Visão geral" },
      { viewId: "my_tasks", label: "Minhas tarefas" },
      { viewId: "customers", label: "Minha Carteira" },
      { viewId: "proposals", label: "Propostas comerciais" },
      { viewId: "analytics_otd", label: "Pontualidade (OTD)" },
    ];
    for (const item of extras) {
      pushRecentView(item);
    }
    assert.equal(readRecentViews().length, 5);
  });

  it("filtra por capabilities", () => {
    const filtered = filterRecentsByCaps(
      [
        { viewId: "proposals", label: "Propostas comerciais", at: 1 },
        { viewId: "open_orders", label: "Meus pedidos", at: 2 },
      ],
      {
        analytics: false,
        worklist: false,
        proposals: false,
        customers: false,
        admin: false,
      },
    );
    assert.deepEqual(
      filtered.map((item) => item.viewId),
      ["open_orders"],
    );
  });
});
