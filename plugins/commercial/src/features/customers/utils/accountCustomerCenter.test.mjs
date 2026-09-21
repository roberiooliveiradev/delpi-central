import assert from "node:assert/strict";
import { after, before, describe, it } from "node:test";

import {
  resolveAccountCustomerCenter,
  writeAccountCustomerCenter,
} from "./accountCustomerCenter.ts";

const memory = new Map();
const fakeWindow = {
  sessionStorage: {
    getItem: (key) => (memory.has(key) ? memory.get(key) : null),
    setItem: (key, value) => {
      memory.set(key, String(value));
    },
    removeItem: (key) => {
      memory.delete(key);
    },
  },
};

describe("resolveAccountCustomerCenter", () => {
  before(() => {
    globalThis.window = fakeWindow;
  });
  after(() => {
    memory.clear();
    delete globalThis.window;
  });

  it("usa o centro da sessao sem colocar na URL", () => {
    writeAccountCustomerCenter("000001", "01", "1100");
    assert.equal(
      resolveAccountCustomerCenter({
        codigo: "000001",
        loja: "01",
        portfolios: [],
      }),
      "1100",
    );
    writeAccountCustomerCenter("000001", "01", null);
  });

  it("quando a membership tem um unico centro, usa esse centro", () => {
    writeAccountCustomerCenter("000001", "11", null);
    assert.equal(
      resolveAccountCustomerCenter({
        codigo: "000001",
        loja: "11",
        portfolios: [
          {
            id: "p1",
            user_id: "u1",
            display_name: "WEG",
            active: true,
            customer_count: 1,
            customers: [
              {
                customer_code: "000001",
                customer_store: "11",
                customer_name: "WEG AUTOMACAO",
                customer_center: "1320",
              },
            ],
          },
        ],
      }),
      "1320",
    );
  });

  it("com dois centros no mesmo par, sem sessao, mantem a loja inteira", () => {
    writeAccountCustomerCenter("000001", "01", null);
    assert.equal(
      resolveAccountCustomerCenter({
        codigo: "000001",
        loja: "01",
        portfolios: [
          {
            id: "p1",
            user_id: "u1",
            display_name: "WEG",
            active: true,
            customer_count: 2,
            customers: [
              {
                customer_code: "000001",
                customer_store: "01",
                customer_name: "WEG",
                customer_center: "1100",
              },
              {
                customer_code: "000001",
                customer_store: "01",
                customer_name: "WEG",
                customer_center: "1200",
              },
            ],
          },
        ],
      }),
      "",
    );
  });
});
