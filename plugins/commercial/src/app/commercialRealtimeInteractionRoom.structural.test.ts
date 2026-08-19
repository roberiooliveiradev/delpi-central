import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("CommercialRealtimeProvider interaction room", () => {
  it("expõe join/leave/subscribe e reenvia subscribe no open", () => {
    const source = readFileSync(join(dir, "CommercialRealtimeProvider.tsx"), "utf8");
    expect(source).toMatch(/joinInteractionRoom/);
    expect(source).toMatch(/leaveInteractionRoom/);
    expect(source).toMatch(/subscribeInteractionRoomEvents/);
    expect(source).toMatch(/useInteractionRoomSync/);
    expect(source).toMatch(/useInteractionInboxSync/);
    expect(source).toMatch(/buildInteractionRoomSubscribePayload/);
    expect(source).toMatch(/desiredInteractionRoomIdsRef/);
    expect(source).toMatch(/isInteractionRoomEventType/);
  });
});
