import { describe, expect, it } from "vitest";

import type { CollaborationPresencePayload } from "../data/api/transformometroCollaborationApi";
import { isMatchingPresencePayload } from "./collaborationPresence";

const sample: CollaborationPresencePayload = {
  entity_type: "processo",
  entity_id: "29157fc0-a2e1-402e-a259-29390c61c0d4",
  viewers: [],
  editors: [],
};

describe("isMatchingPresencePayload", () => {
  it("aceita payload da mesma entidade", () => {
    expect(
      isMatchingPresencePayload(sample, "processo", "29157fc0-a2e1-402e-a259-29390c61c0d4")
    ).toBe(true);
  });

  it("rejeita entity_id ou entity_type diferentes", () => {
    expect(isMatchingPresencePayload(sample, "processo_instancia", sample.entity_id)).toBe(false);
    expect(isMatchingPresencePayload(sample, "processo", "outro-id")).toBe(false);
  });
});
