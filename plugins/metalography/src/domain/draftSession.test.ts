import { describe, expect, it } from "vitest";

import { clearKey, idempotencyKey } from "./draftSession";

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key) => values.get(key) ?? null,
    key: (index) => [...values.keys()][index] ?? null,
    removeItem: (key) => values.delete(key),
    setItem: (key, value) => values.set(key, value),
  };
}

describe("idempotency", () => {
  it("reuses the same key until it is cleared", () => {
    const storage = memoryStorage();
    const first = idempotencyKey(storage, "create", () => "key-123456");
    const second = idempotencyKey(storage, "create", () => "other-key");
    expect(second).toBe(first);
    clearKey(storage, "create");
    expect(idempotencyKey(storage, "create", () => "next-key-1")).toBe("next-key-1");
  });
});
