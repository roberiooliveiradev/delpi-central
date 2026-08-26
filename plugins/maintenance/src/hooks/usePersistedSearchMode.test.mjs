#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it, beforeEach, afterEach } from "node:test";

import {
  isSearchMode,
  readStoredSearchMode,
} from "./usePersistedSearchMode.ts";

const STORAGE_KEY = "maintenance:test:search-mode:v1";

function installLocalStorageMock() {
  const store = new Map();
  globalThis.localStorage = {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => {
      store.set(key, value);
    },
    removeItem: (key) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
    key: (index) => Array.from(store.keys())[index] ?? null,
    get length() {
      return store.size;
    },
  };
}

describe("usePersistedSearchMode storage", () => {
  beforeEach(() => {
    installLocalStorageMock();
    globalThis.window = globalThis;
  });

  afterEach(() => {
    delete globalThis.localStorage;
    delete globalThis.window;
  });

  it("isSearchMode aceita tool e part", () => {
    assert.equal(isSearchMode("tool"), true);
    assert.equal(isSearchMode("part"), true);
    assert.equal(isSearchMode("ferramenta"), false);
    assert.equal(isSearchMode(""), false);
  });

  it("readStoredSearchMode retorna null sem valor", () => {
    assert.equal(readStoredSearchMode(STORAGE_KEY), null);
  });

  it("readStoredSearchMode lê valor válido", () => {
    localStorage.setItem(STORAGE_KEY, "part");
    assert.equal(readStoredSearchMode(STORAGE_KEY), "part");
  });

  it("readStoredSearchMode ignora valor inválido", () => {
    localStorage.setItem(STORAGE_KEY, "invalid");
    assert.equal(readStoredSearchMode(STORAGE_KEY), null);
  });
});
