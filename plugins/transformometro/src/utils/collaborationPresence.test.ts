import { describe, expect, it } from "vitest";

import type { CollaborationPresencePayload } from "../data/api/transformometroCollaborationApi";
import { isMatchingPresencePayload, presencePayloadEquals } from "./collaborationPresence";

const sample: CollaborationPresencePayload = {
  entity_type: "processo",
  entity_id: "29157fc0-a2e1-402e-a259-29390c61c0d4",
  viewers: [],
  editors: [],
};

describe("presencePayloadEquals", () => {
  it("retorna true para snapshots semanticamente iguais", () => {
    const left: CollaborationPresencePayload = {
      ...sample,
      viewers: [
        {
          user_id: "u1",
          user_name: "Ana",
          section_key: "",
          mode: "viewing",
        },
      ],
    };
    const right: CollaborationPresencePayload = {
      ...sample,
      viewers: [
        {
          user_id: "u1",
          user_name: "Ana",
          section_key: "",
          mode: "viewing",
        },
      ],
    };
    expect(presencePayloadEquals(left, right)).toBe(true);
  });

  it("retorna false quando a lista de editores muda", () => {
    const left: CollaborationPresencePayload = { ...sample, editors: [] };
    const right: CollaborationPresencePayload = {
      ...sample,
      editors: [
        {
          user_id: "u2",
          user_name: "Bob",
          section_key: "diagrama_macro",
          mode: "editing",
          lock_active: true,
        },
      ],
    };
    expect(presencePayloadEquals(left, right)).toBe(false);
  });
});

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
