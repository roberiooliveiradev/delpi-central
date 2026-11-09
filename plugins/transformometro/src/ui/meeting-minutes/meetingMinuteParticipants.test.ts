import { describe, expect, it } from "vitest";

import {
  draftFromDirectoryUser,
  hydrateParticipantsFromDetail,
  isSigner,
} from "./meetingMinuteParticipants";

describe("hydrateParticipantsFromDetail", () => {
  it("marks name-only internals as unresolved and never as signers", () => {
    const drafts = hydrateParticipantsFromDetail(
      [
        {
          display_name: "Robério Teixeira de Oliveira",
          must_sign: false,
          is_external: false,
          user_id: null,
          role_in_meeting: "other",
        },
        {
          display_name: "Joici Motta",
          must_sign: true,
          is_external: false,
          user_id: null,
        },
      ],
      [],
    );
    expect(drafts).toHaveLength(2);
    expect(drafts.every((d) => d.unresolved_identity)).toBe(true);
    expect(drafts.every((d) => d.must_sign === false)).toBe(true);
    expect(drafts.filter(isSigner)).toHaveLength(0);
  });

  it("keeps directory-linked must_sign as signer", () => {
    const drafts = hydrateParticipantsFromDetail(
      [
        {
          user_id: "11111111-1111-1111-1111-111111111111",
          display_name: "Ana",
          must_sign: true,
          is_external: false,
        },
      ],
      [
        {
          user_id: "11111111-1111-1111-1111-111111111111",
          display_name: "Ana",
        },
      ],
    );
    expect(drafts[0].unresolved_identity).toBeUndefined();
    expect(isSigner(drafts[0])).toBe(true);
  });
});

describe("draftFromDirectoryUser", () => {
  it("links unresolved name when re-selected from directory", () => {
    const orphan = hydrateParticipantsFromDetail(
      [{ display_name: "Ana", user_id: null, must_sign: false }],
      [],
    )[0];
    const linked = draftFromDirectoryUser(
      { id: "11111111-1111-1111-1111-111111111111", name: "Ana" },
      orphan,
    );
    expect(linked.user_id).toBe("11111111-1111-1111-1111-111111111111");
    expect(linked.unresolved_identity).toBeUndefined();
    expect(linked.must_sign).toBe(true);
    expect(isSigner(linked)).toBe(true);
  });
});
