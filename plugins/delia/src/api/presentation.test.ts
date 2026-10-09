import { describe, expect, it } from "vitest";

import {
  dedupeOwnerHintContent,
  parsePresentation,
  presentationOwnerHint,
} from "./presentation";

const BASE_PRESENTATION = {
  version: "1",
  message_kind: "RESULT",
  semantic_status: "OBSERVATION",
  grounding_status: "GROUNDED",
  blocks: [{ kind: "text", text: "conteúdo" }],
  allowed_interactions: ["reply"],
};

describe("parsePresentation", () => {
  it("parses a canonical RESULT presentation", () => {
    const parsed = parsePresentation(BASE_PRESENTATION);
    expect(parsed).not.toBeNull();
    expect(parsed?.messageKind).toBe("RESULT");
    expect(parsed?.semanticStatus).toBe("OBSERVATION");
    expect(parsed?.groundingStatus).toBe("GROUNDED");
    expect(parsed?.blocks).toEqual([{ kind: "text", text: "conteúdo" }]);
    expect(parsed?.allowedInteractions).toEqual(["reply"]);
  });

  it.each([
    "RESULT",
    "CLARIFICATION_REQUIRED",
    "CONFIRMATION_REQUIRED",
    "WRITE_REJECTED",
    "AUTHZ_DENIED",
    "SOURCE_UNAVAILABLE",
    "PRECONDITION_REQUIRED",
  ])("preserves the canonical kind %s", (kind) => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      message_kind: kind,
    });
    expect(parsed?.messageKind).toBe(kind);
  });

  it("does not force RESULT on an unknown message kind", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      message_kind: "SECRET_INTERNAL_KIND",
    });
    expect(parsed).not.toBeNull();
    expect(parsed?.messageKind).toBeNull();
  });

  it("falls back to null on an unknown contract version", () => {
    expect(
      parsePresentation({ ...BASE_PRESENTATION, version: "2" }),
    ).toBeNull();
    expect(
      parsePresentation({ ...BASE_PRESENTATION, version: 1 }),
    ).toBeNull();
  });

  it.each([null, undefined, "x", 42, [1, 2]])(
    "returns null on malformed payload %j",
    (raw) => {
      expect(parsePresentation(raw)).toBeNull();
    },
  );

  it("drops unknown block kinds and unknown notice roles", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      blocks: [
        { kind: "text", text: "ok" },
        { kind: "chart", data: { evil: true } },
        { kind: "notice", role: "authorize_url", text: "https://x" },
        { kind: "notice", role: "owner_hint", text: "vincule a conta" },
      ],
    });
    expect(parsed?.blocks).toEqual([
      { kind: "text", text: "ok" },
      { kind: "notice", role: "owner_hint", text: "vincule a conta" },
    ]);
  });

  it("drops blocks with non-string text", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      blocks: [
        { kind: "text", text: { nested: true } },
        { kind: "text", text: "válido" },
      ],
    });
    expect(parsed?.blocks).toEqual([{ kind: "text", text: "válido" }]);
  });

  it("keeps raw text verbatim — HTML/JS stays inert string", () => {
    const hostile = '<img src=x onerror=alert(1)><script>alert(2)</script>';
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      blocks: [
        { kind: "text", text: hostile },
        { kind: "notice", role: "owner_hint", text: hostile },
      ],
    });
    expect(parsed?.blocks[0]).toEqual({ kind: "text", text: hostile });
    expect(presentationOwnerHint(parsed)).toBe(hostile);
  });

  it("bounds block count and block text", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      blocks: Array.from({ length: 12 }, (_, i) => ({
        kind: "text",
        text: `b${i}`,
      })),
    });
    expect(parsed?.blocks).toHaveLength(8);

    const long = "x".repeat(20_000);
    const bounded = parsePresentation({
      ...BASE_PRESENTATION,
      blocks: [{ kind: "text", text: long }],
    });
    expect(bounded?.blocks[0]?.text).toHaveLength(16_384);
  });

  it("filters allowed_interactions to the known vocabulary", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      message_kind: "CONFIRMATION_REQUIRED",
      allowed_interactions: ["reply", "confirm", "reject", "act", 7],
    });
    expect(parsed?.allowedInteractions).toEqual([
      "reply",
      "confirm",
      "reject",
    ]);
  });

  it("maps an owner-hint notice to presentationOwnerHint", () => {
    const parsed = parsePresentation({
      ...BASE_PRESENTATION,
      message_kind: "PRECONDITION_REQUIRED",
      blocks: [
        { kind: "text", text: "Não foi possível concluir." },
        {
          kind: "notice",
          role: "owner_hint",
          text: "Helpdesk BFF error: glpi_link_required.",
        },
      ],
    });
    expect(presentationOwnerHint(parsed)).toBe(
      "Helpdesk BFF error: glpi_link_required.",
    );
    expect(presentationOwnerHint(parsePresentation(BASE_PRESENTATION))).toBeNull();
  });
});

describe("dedupeOwnerHintContent", () => {
  it("strips the exact legacy owner-hint suffix once", () => {
    const content =
      "Não foi possível concluir. A fonte informou: glpi_link_required.";
    expect(
      dedupeOwnerHintContent(content, "glpi_link_required."),
    ).toBe("Não foi possível concluir.");
  });

  it("leaves content untouched when the suffix is absent", () => {
    const content = "Resposta normal sem hint.";
    expect(
      dedupeOwnerHintContent(content, "glpi_link_required."),
    ).toBe(content);
    expect(dedupeOwnerHintContent(content, null)).toBe(content);
  });

  it("leaves content untouched when the hint is embedded mid-text", () => {
    const content = "A fonte informou: glpi_link_required. e mais texto";
    expect(
      dedupeOwnerHintContent(content, "glpi_link_required."),
    ).toBe(content);
  });
});
