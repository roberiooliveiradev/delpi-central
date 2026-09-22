import { describe, expect, it } from "vitest";

import { detectActiveMention } from "../collaboration/mentionComposerCaret";
import {
  buildGlpiUserMentionLabel,
  createGlpiUserMentionElement,
  insertGlpiUserMentionAtPlainRange,
  isGlpiUserMentionId,
} from "./richTextUserMention";

describe("richTextUserMention", () => {
  it("aceita só id numérico", () => {
    expect(isGlpiUserMentionId("69")).toBe(true);
    expect(isGlpiUserMentionId("abc")).toBe(false);
    expect(isGlpiUserMentionId("")).toBe(false);
  });

  it("normaliza label com @", () => {
    expect(buildGlpiUserMentionLabel("Ana Silva")).toBe("@Ana Silva");
    expect(buildGlpiUserMentionLabel("@Ana")).toBe("@Ana");
  });

  it("cria span data-user-mention + data-user-id", () => {
    const span = createGlpiUserMentionElement(document, {
      userId: "42",
      label: "Ana",
    });
    expect(span).toBeTruthy();
    expect(span!.getAttribute("data-user-mention")).toBe("true");
    expect(span!.getAttribute("data-user-id")).toBe("42");
    expect(span!.getAttribute("contenteditable")).toBe("false");
    expect(span!.textContent).toBe("@Ana");
  });

  it("recusa id não numérico na criação", () => {
    expect(
      createGlpiUserMentionElement(document, { userId: "x", label: "Ana" }),
    ).toBeNull();
  });

  it("insere span no range @query e deixa espaço após", () => {
    const root = document.createElement("div");
    const p = document.createElement("p");
    p.textContent = "Oi @An";
    root.appendChild(p);
    document.body.appendChild(root);

    const active = detectActiveMention("Oi @An", 6);
    expect(active).toEqual({ query: "An", start: 3, end: 6 });

    const ok = insertGlpiUserMentionAtPlainRange(root, active!.start, active!.end, {
      id: "69",
      label: "Ana",
    });
    expect(ok).toBe(true);
    const span = root.querySelector("span[data-user-id='69']");
    expect(span).toBeTruthy();
    expect(span!.getAttribute("data-user-mention")).toBe("true");
    expect(span!.textContent).toBe("@Ana");
    expect(root.textContent).toMatch(/Oi @Ana /);

    root.remove();
  });

  it("não detecta @ no meio da palavra (negativo)", () => {
    expect(detectActiveMention("email@An", 8)).toBeNull();
  });

  it("detecta segundo @ após menção (sibling)", () => {
    expect(detectActiveMention("Oi @Ana @Br", 11)).toEqual({
      query: "Br",
      start: 8,
      end: 11,
    });
  });
});
