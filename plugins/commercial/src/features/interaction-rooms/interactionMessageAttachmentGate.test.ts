import { describe, expect, it } from "vitest";

import {
  gatePendingAttachments,
  interactionMessageLooksLikeRawHtml,
} from "./interactionMessageAttachmentGate";

describe("interactionMessageLooksLikeRawHtml", () => {
  it("aceita markdown e inline permitido", () => {
    expect(interactionMessageLooksLikeRawHtml("**oi** e `x`")).toBe(false);
    expect(interactionMessageLooksLikeRawHtml("texto <u>sub</u>")).toBe(false);
    expect(
      interactionMessageLooksLikeRawHtml('<span style="font-size: 18px">a</span>'),
    ).toBe(false);
  });

  it("rejeita HTML cru", () => {
    expect(interactionMessageLooksLikeRawHtml("<p>oi</p>")).toBe(true);
    expect(interactionMessageLooksLikeRawHtml("<script>x</script>")).toBe(true);
  });
});

describe("gatePendingAttachments", () => {
  it("recusa quando passa do teto de quantidade", () => {
    const result = gatePendingAttachments(9, [
      new File(["a"], "a.pdf", { type: "application/pdf" }),
      new File(["b"], "b.pdf", { type: "application/pdf" }),
    ]);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toMatch(/10/);
  });

  it("recusa arquivo acima do teto de bytes", () => {
    const big = new File([new Uint8Array(21 * 1024 * 1024)], "big.pdf", {
      type: "application/pdf",
    });
    const result = gatePendingAttachments(0, [big]);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toMatch(/20/);
  });

  it("aceita dentro do teto", () => {
    const file = new File(["ok"], "ok.pdf", { type: "application/pdf" });
    const result = gatePendingAttachments(0, [file]);
    expect(result).toEqual({ ok: true, files: [file] });
  });
});
