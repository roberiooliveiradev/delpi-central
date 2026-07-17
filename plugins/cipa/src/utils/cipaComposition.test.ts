import { describe, expect, it } from "vitest";

import {
  membersToParticipantDrafts,
  mergeCompositionWithExternals,
} from "./cipaComposition";

const members = [
  {
    id: "m1",
    unit_code: "01",
    user_id: "11111111-1111-1111-1111-111111111111",
    display_name: "Ana",
    role: "president",
    mandate_start: "2026-01-01",
    is_active: true,
  },
  {
    id: "m2",
    unit_code: "01",
    user_id: "22222222-2222-2222-2222-222222222222",
    display_name: "Bruno",
    role: "secretary",
    mandate_start: "2026-01-01",
    is_active: true,
  },
];

describe("cipaComposition", () => {
  it("pré-carrega membros com cargo e assinatura obrigatória", () => {
    const drafts = membersToParticipantDrafts(members);
    expect(drafts).toHaveLength(2);
    expect(drafts[0]).toMatchObject({
      user_id: members[0].user_id,
      display_name: "Ana",
      role_in_meeting: "president",
      must_sign: true,
      is_external: false,
    });
  });

  it("preserva externos ao recarregar composição", () => {
    const current = [
      {
        user_id: "old",
        display_name: "Antigo",
        role_in_meeting: "titular_member",
        presence: "present",
        is_external: false,
        must_sign: true,
      },
      {
        display_name: "Convidado",
        role_in_meeting: "guest",
        presence: "present",
        is_external: true,
        must_sign: false,
      },
    ];
    const merged = mergeCompositionWithExternals(members, current);
    expect(merged.map((item) => item.display_name)).toEqual([
      "Ana",
      "Bruno",
      "Convidado",
    ]);
  });
});
