import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { readHomeSearchQuery, writeHomeSearchQuery } from "./homeSearchQuery.ts";

function installWindowMock(initialUrl = "http://localhost/apps/commercial") {
  const url = new URL(initialUrl);
  const location = {
    get href() {
      return url.href;
    },
    get pathname() {
      return url.pathname;
    },
    get search() {
      return url.search;
    },
    get hash() {
      return url.hash;
    },
  };
  globalThis.window = {
    location,
    history: {
      state: null,
      replaceState(_state, _title, next) {
        const updated = new URL(String(next), url.origin);
        url.pathname = updated.pathname;
        url.search = updated.search;
        url.hash = updated.hash;
      },
    },
  };
}

describe("homeSearchQuery", () => {
  it("lê q da query string", () => {
    assert.equal(readHomeSearchQuery("?q=propostas"), "propostas");
    assert.equal(readHomeSearchQuery("?foo=1"), "");
  });

  it("grava e remove q via replaceState", () => {
    installWindowMock();
    writeHomeSearchQuery("ady");
    assert.match(window.location.search, /q=ady/);
    writeHomeSearchQuery("");
    assert.equal(new URLSearchParams(window.location.search).has("q"), false);
  });
});
