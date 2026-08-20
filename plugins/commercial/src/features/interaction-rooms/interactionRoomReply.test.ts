import { describe, expect, it } from "vitest";

import {
  buildReplyComposerBanner,
  truncateReplyPreview,
} from "./interactionRoomReply";

describe("interactionRoomReply", () => {
  it("trunca preview longo", () => {
    expect(truncateReplyPreview("olá")).toBe("olá");
    expect(truncateReplyPreview("x".repeat(200)).endsWith("…")).toBe(true);
    expect(truncateReplyPreview("x".repeat(200)).length).toBeLessThanOrEqual(120);
  });

  it("monta faixa Respondendo a {author}", () => {
    const banner = buildReplyComposerBanner(
      {
        id: "m1",
        room_id: "r1",
        message_kind: "text",
        body_text: "Oi mundo",
        author_user_id: "u1",
      },
      "Ana",
    );
    expect(banner?.label).toBe("Respondendo a Ana");
    expect(banner?.preview).toBe("Oi mundo");
  });

  it("usa fallback sem autor", () => {
    const banner = buildReplyComposerBanner(
      {
        id: "m1",
        room_id: "r1",
        message_kind: "text",
        body_text: "",
      },
      null,
    );
    expect(banner?.label).toBe("Respondendo");
    expect(banner?.preview).toBeUndefined();
  });
});
