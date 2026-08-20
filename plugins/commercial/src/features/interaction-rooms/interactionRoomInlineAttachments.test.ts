import { describe, expect, it } from "vitest";

import {
  countFilesTowardAttachmentCap,
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "./interactionRoomInlineAttachments";

describe("interactionRoomInlineAttachments", () => {
  it("lista pending e uuids", () => {
    const md =
      "![a](attachment:pending:p1) ![b](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)";
    expect(listInlinePendingIdsFromMarkdown(md)).toEqual(["p1"]);
    expect(listInlineAttachmentIdsFromMarkdown(md)).toEqual([
      "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    ]);
  });

  it("reescreve pending", () => {
    expect(
      rewriteInlinePendingInMarkdown("x ![s](attachment:pending:local-1) y", {
        "local-1": "11111111-2222-3333-4444-555555555555",
      }),
    ).toBe("x ![s](attachment:11111111-2222-3333-4444-555555555555) y");
  });

  it("soma teto anexo+inline", () => {
    expect(countFilesTowardAttachmentCap(3, 2)).toBe(5);
  });
});
