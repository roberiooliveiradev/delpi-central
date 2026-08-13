import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  fanPresenceUpdated,
  subscribePresenceWithReplay,
} from "./commercialPresenceSubscribe.ts";

describe("commercialPresenceSubscribe", () => {
  it("replay no subscribe tardio após snapshot sem handlers", () => {
    const last = { current: null };
    const handlers = new Set();
    fanPresenceUpdated(last, handlers, {
      type: "presence.updated",
      onlineUserIds: ["u-self", "u2"],
    });
    assert.equal(handlers.size, 0);
    assert.deepEqual(last.current?.onlineUserIds, ["u-self", "u2"]);

    const seen = [];
    const unsubscribe = subscribePresenceWithReplay(last, handlers, (event) => {
      seen.push([...event.onlineUserIds]);
    });
    assert.deepEqual(seen, [["u-self", "u2"]]);
    unsubscribe();
    assert.equal(handlers.size, 0);
  });

  it("fan-out notifica handlers já inscritos", () => {
    const last = { current: null };
    const handlers = new Set();
    const seen = [];
    subscribePresenceWithReplay(last, handlers, (event) => {
      seen.push(event.onlineUserIds.join(","));
    });
    assert.deepEqual(seen, []);
    fanPresenceUpdated(last, handlers, {
      type: "presence.updated",
      onlineUserIds: ["a"],
    });
    assert.deepEqual(seen, ["a"]);
  });
});
