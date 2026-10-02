import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const appHost = readFileSync(
  path.join(path.dirname(fileURLToPath(import.meta.url)), "AppHost.tsx"),
  "utf8",
);

describe("AppHost federated unmount", () => {
  it("captures the host element before cleanup, when React has not cleared the ref yet", () => {
    const effectStart = appHost.indexOf("const mountEl = federatedHostRef.current;");
    const cleanupStart = appHost.indexOf("return () => {\n      isActive = false;");
    assert.ok(effectStart >= 0);
    assert.ok(cleanupStart > effectStart);
    const cleanupEnd = appHost.indexOf("}, [app?.id, app?.renderMode, federationEntry, getAccessToken]);", cleanupStart);
    assert.ok(cleanupEnd > cleanupStart);
    const cleanup = appHost.slice(cleanupStart, cleanupEnd);
    assert.match(cleanup, /unmountFederatedRemote\(mounted, mountEl\)/);
    assert.doesNotMatch(cleanup, /federatedHostRef\.current/);
  });
});
