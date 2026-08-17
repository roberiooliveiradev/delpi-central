import assert from "node:assert/strict";
import { describe, it, beforeEach } from "node:test";

import {
  clearImportantNotificationSnooze,
  isImportantNotificationSnoozed,
  shouldBreakImportantNotificationSnooze,
  snoozeImportantNotificationOverlay,
} from "./importantNotificationSnooze";

function installMemorySessionStorage() {
  const store = new Map<string, string>();
  const memory = {
    getItem(key: string) {
      return store.has(key) ? store.get(key)! : null;
    },
    setItem(key: string, value: string) {
      store.set(key, String(value));
    },
    removeItem(key: string) {
      store.delete(key);
    },
    clear() {
      store.clear();
    },
  };
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: memory,
  });
}

describe("importantNotificationSnooze", () => {
  beforeEach(() => {
    installMemorySessionStorage();
    clearImportantNotificationSnooze();
  });

  it("adiar oculta overlay por duração", () => {
    const now = 1_000_000;
    snoozeImportantNotificationOverlay(["a"], 60_000, now);
    assert.equal(isImportantNotificationSnoozed(now + 1), true);
    assert.equal(isImportantNotificationSnoozed(now + 60_001), false);
  });

  it("nova importante quebra o snooze", () => {
    const now = 1_000_000;
    snoozeImportantNotificationOverlay(["a"], 60_000, now);
    assert.equal(shouldBreakImportantNotificationSnooze(["a"], now + 1), false);
    assert.equal(shouldBreakImportantNotificationSnooze(["a", "b"], now + 1), true);
  });
});
