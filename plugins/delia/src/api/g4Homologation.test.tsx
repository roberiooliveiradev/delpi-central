/**
 * G4 — consumer-side integrated homologation over REAL producer output.
 *
 * DELIA-C3-MARKDOWN-B2-G4-INTEGRATED-ACCEPTANCE-01 (CP-333).
 *
 * The fixture in __fixtures__/g4-wire-envelopes.json is emitted by the
 * real backend chain (render_specialist_outcome_rich →
 * InteractiveTurnResult → compose_presentation → serialize_result);
 * the backend suite asserts byte-equality between this fixture and a
 * fresh emission, so consumer evidence here binds to the real wire.
 *
 * Renderer semantics are proven through the REAL shared renderer —
 * ConversationMarkdown + conversationMarkdownToPlainText from the
 * federated plugin-ui barrel — never a reimplemented lexer.
 */

import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  parsePresentationV2,
  presentationMarkdownSource,
  presentationPrimaryTextFormat,
  parsePresentation,
} from "./presentation";
import {
  ConversationMarkdown,
  conversationMarkdownToPlainText,
} from "@delpi/plugin-ui/index";

type WireBody = {
  content: string;
  presentation: Record<string, unknown>;
};

const fixture = JSON.parse(
  readFileSync(
    resolve(process.cwd(), "src/api/__fixtures__/g4-wire-envelopes.json"),
    "utf-8",
  ),
) as {
  structured: WireBody;
  hostile: WireBody;
  plain: WireBody;
};

function markdownFromWire(body: WireBody): string {
  const parsed = parsePresentationV2(body.presentation);
  expect(parsed.status).toBe("ok");
  if (parsed.status !== "ok") throw new Error("v2 parse failed");
  const md = presentationMarkdownSource(parsed.presentation);
  expect(md).not.toBeNull();
  return md ?? "";
}

afterEach(cleanup);

describe("G4 — real wire → v2 reader", () => {
  it("admits the emitted structured envelope as markdown_safe", () => {
    const parsed = parsePresentationV2(fixture.structured.presentation);
    expect(parsed.status).toBe("ok");
    if (parsed.status !== "ok") return;
    expect(presentationPrimaryTextFormat(parsed.presentation)).toBe(
      "markdown_safe",
    );
    const md = presentationMarkdownSource(parsed.presentation);
    expect(md).not.toBeNull();
  });

  it("v1 envelope is not_v2 — legacy parser stays owner", () => {
    expect(parsePresentationV2(fixture.plain.presentation).status).toBe(
      "not_v2",
    );
    const v1 = parsePresentation(fixture.plain.presentation);
    expect(v1).not.toBeNull();
    expect(v1?.blocks[0]).toMatchObject({
      kind: "text",
      text: "Lote L-88 conferido.",
    });
    expect(v1?.blocks[0]).not.toHaveProperty("format");
  });

  it("v2 wire keeps top-level content for legacy clients", () => {
    expect(fixture.structured.content).toContain("OP-10293");
    expect(fixture.structured.content).toContain("150.5");
  });
});

describe("G4 — fidelity of business data", () => {
  it("preserves identifiers, quantities, units and order", () => {
    const literal = markdownFromWire(fixture.structured).replace(/\\/g, "");
    for (const token of [
      "OP-10293",
      "OP-10294",
      "PA-771",
      "PA-772",
      "150.5",
      "KG",
      "3",
      "UN",
    ]) {
      expect(literal).toContain(token);
    }
    expect(literal.indexOf("OP-10293")).toBeLessThan(
      literal.indexOf("OP-10294"),
    );
  });
});

describe("G4 — hostile leaves through the REAL shared renderer", () => {
  const hostileMd = () => markdownFromWire(fixture.hostile);

  function renderMarkdown(source: string) {
    return render(
      <ConversationMarkdown
        text={source}
        enabled={true}
        authorizedLinks={[]}
      />,
    );
  }

  it("produces zero structural nodes beyond the projector's lists", () => {
    const { container } = renderMarkdown(hostileMd());
    // Projector-authorized structure: ordered + unordered lists only.
    expect(container.querySelectorAll("ul, ol").length).toBeGreaterThan(0);
    // No owner leaf may have created its own structure.
    expect(container.querySelector("h1, h2, h3, h4, h5, h6")).toBeNull();
    expect(container.querySelector("blockquote")).toBeNull();
    expect(container.querySelector("pre, code.delpi-ui-conversation-code-block")).toBeNull();
    expect(container.querySelector("table")).toBeNull();
    expect(container.querySelector("hr")).toBeNull();
    expect(container.querySelector("iframe, svg, script")).toBeNull();
  });

  it("produces zero navigable links — autolinks stay inert", () => {
    const { container } = renderMarkdown(hostileMd());
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toContain("https://evil.example");
    expect(container.textContent).toContain("www.auto.example");
  });

  it("HTML/script/SVG payloads render as inert text, never elements", () => {
    const { container } = renderMarkdown(hostileMd());
    expect(container.querySelector("script, iframe, svg, object, embed")).toBeNull();
    expect(container.textContent).toContain("<script>");
  });

  it("forged heading/list/quote lines stay inside the leaf line", () => {
    const { container } = renderMarkdown(hostileMd());
    const lists = container.querySelectorAll("li");
    const leafText = Array.from(lists)
      .map((li) => li.textContent ?? "")
      .join("\n");
    expect(leafText).toContain("# Forged Heading");
    expect(leafText).toContain("forged item");
    expect(leafText).toContain("forged quote");
  });
});

describe("G4 — clipboard projection contract", () => {
  it("copies literal text: IDs/units/order intact, zero markdown syntax", () => {
    const md = markdownFromWire(fixture.structured);
    const plain = conversationMarkdownToPlainText(md, []);
    expect(plain).not.toBeNull();
    expect(plain).toContain("OP-10293");
    expect(plain).toContain("PA-771");
    expect(plain).toContain("150.5");
    expect(plain).toContain("KG");
    expect(plain).not.toContain("\\");
    expect(plain).not.toContain("**");
    expect((plain ?? "").indexOf("OP-10293")).toBeLessThan(
      (plain ?? "").indexOf("OP-10294"),
    );
  });

  it("copied hostile content keeps literals but never destinations", () => {
    const md = markdownFromWire(fixture.hostile);
    const plain = conversationMarkdownToPlainText(md, []);
    expect(plain).not.toBeNull();
    // Owner text survives as words; no link destination is emitted as
    // an authorized `label (href)` pair because nothing was admitted.
    expect(plain).toContain("evil.example");
    expect(plain).not.toContain("] (");
  });
});

describe("G4 — compatibility and rollback", () => {
  it("v2 envelope with a missing format fails closed", () => {
    const bad = {
      ...fixture.structured.presentation,
      blocks: [{ kind: "text", text: "no format" }],
    };
    expect(parsePresentationV2(bad).status).toBe("neutral_error");
  });

  it("unknown version never coerces into v2", () => {
    const bad = { ...fixture.structured.presentation, version: "3" };
    expect(parsePresentationV2(bad).status).toBe("not_v2");
  });

  it("unexpected block kind fails closed", () => {
    const bad = {
      ...fixture.structured.presentation,
      blocks: [{ kind: "artifact", format: "markdown_safe", text: "x" }],
    };
    expect(parsePresentationV2(bad).status).toBe("neutral_error");
  });

  it("invalid markdown_safe declaration fails closed", () => {
    const bad = {
      ...fixture.structured.presentation,
      blocks: [{ kind: "text", format: "markdown_any", text: "x" }],
    };
    expect(parsePresentationV2(bad).status).toBe("neutral_error");
  });
});


describe("Conversational admission — real producer conversational envelope", () => {
  // CP-333 decision f09acc8544: the governed conversational
  // COMPOSITION_MODEL result is now admitted to the same v2
  // markdown_safe channel — same envelope shape, NON_GROUNDED, no
  // provenance. The consumer treats it identically to governed
  // Category-A markdown_safe: bounded tokens, authorizedLinks gate.
  const conversationalEnvelope = {
    version: "2",
    message_kind: "RESULT",
    semantic_status: "HYPOTHESIS",
    grounding_status: "NON_GROUNDED",
    blocks: [
      {
        kind: "text",
        format: "markdown_safe",
        text:
          "A metodologia SIPOC organiza o processo em cinco etapas:\n\n" +
          "**1. Suppliers (Fornecedores)**\n" +
          "- Identificam quem fornece os insumos.\n\n" +
          "**3. Process (Processo)**\n" +
          "1. Recebimento do material.\n" +
          "2. Usinagem da peca.\n\n" +
          "Detalhes em https://unauthorized.example/doc",
      },
    ],
    allowed_interactions: ["reply"],
  };

  it("parsePresentationV2 admits the conversational RESULT envelope", () => {
    const parsed = parsePresentationV2(conversationalEnvelope);
    expect(parsed.status).toBe("ok");
    if (parsed.status !== "ok") return;
    expect(presentationPrimaryTextFormat(parsed.presentation)).toBe(
      "markdown_safe",
    );
    expect(presentationMarkdownSource(parsed.presentation)).toContain(
      "Suppliers",
    );
  });

  it("renders semantic headings/lists/emphasis through ConversationMarkdown", () => {
    const md = markdownFromWire({
      content: "",
      presentation: conversationalEnvelope,
    });
    const { container } = render(
      <ConversationMarkdown
        text={md}
        enabled={true}
        authorizedLinks={[]}
      />,
    );
    expect(
      container.querySelectorAll("ul, ol").length,
    ).toBeGreaterThanOrEqual(2);
    expect(container.querySelectorAll("strong").length).toBeGreaterThan(0);
    // Model-authored URL never becomes navigable without an
    // authorized source — stays inert literal text.
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toContain(
      "https://unauthorized.example/doc",
    );
  });
});
