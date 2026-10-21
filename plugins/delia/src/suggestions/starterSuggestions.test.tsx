import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "../App";
import {
  DELIA_STARTER_SUGGESTIONS,
  resolveStarterSuggestions,
} from "./starterSuggestions";

afterEach(cleanup);

const SUGGESTIONS_SECTION = ".delpi-ui-starter-suggestions";

function suggestionButtons() {
  return document.querySelectorAll<HTMLButtonElement>(
    `${SUGGESTIONS_SECTION} .delpi-ui-starter-suggestions__card`,
  );
}

/** Governed QA mode needs the explicit `?delia-demo=` URL — same
 *  admission as demo turns. */
function renderDemoApp(url = "/apps/delia?delia-demo=simple") {
  const previousUrl = window.location.href;
  window.history.replaceState(null, "", url);
  const rendered = render(<App />);
  return {
    ...rendered,
    restore: () => window.history.replaceState(null, "", previousUrl),
  };
}

describe("resolveStarterSuggestions — governed QA gate (doc 93 §14)", () => {
  it("exposes the four fixtures only while a demo scenario is active", () => {
    expect(resolveStarterSuggestions("simple")).toHaveLength(4);
    expect(resolveStarterSuggestions("activity")).toHaveLength(4);
  });

  it("resolves to [] without an explicit demo scenario — fail-closed", () => {
    expect(resolveStarterSuggestions(null)).toHaveLength(0);
  });

  it("fixtures are honest questions with editable draft text, no capability ids", () => {
    for (const item of DELIA_STARTER_SUGGESTIONS) {
      expect(item.draftText.endsWith("?")).toBe(true);
      expect(item.id).not.toMatch(/mcp|tool|provider|permission/i);
      expect(item.draftText.length).toBeLessThan(200);
    }
  });
});

describe("App — starter suggestions integration (F02-A)", () => {
  it("renders no suggestion section outside governed QA mode", () => {
    const { container } = render(<App />);
    expect(container.querySelector(SUGGESTIONS_SECTION)).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-reception"),
    ).toBeTruthy();
  });

  it("shows the four cards only with an empty conversation", async () => {
    const { container, restore } = renderDemoApp();
    try {
      expect(container.querySelector(SUGGESTIONS_SECTION)).toBeTruthy();
      expect(suggestionButtons()).toHaveLength(4);
      expect(document.body.textContent).toContain(
        "Explore algumas possibilidades para começar",
      );

      // Once a turn exists the reception — and the suggestions — go away.
      const input = screen.getByRole("textbox", {
        name: "Pergunte à DÉLIA",
      });
      fireEvent.change(input, { target: { value: "pergunta qualquer" } });
      fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
      await waitFor(() =>
        expect(
          container.querySelector(SUGGESTIONS_SECTION),
        ).toBeNull(),
      );
      expect(container.querySelector(".delia-timeline")).toBeTruthy();
    } finally {
      restore();
    }
  });

  it("selecting a card fills the draft, focuses the composer, never submits", async () => {
    const { restore } = renderDemoApp();
    try {
      const input = screen.getByRole("textbox", {
        name: "Pergunte à DÉLIA",
      }) as HTMLTextAreaElement;

      fireEvent.click(suggestionButtons()[1]);
      await waitFor(() => expect(input.value).toBe("O que é SIPOC?"));
      await waitFor(() => expect(document.activeElement).toBe(input));
      expect(input.selectionStart).toBe("O que é SIPOC?".length);

      // No user turn, no send — the draft stays editable.
      expect(document.querySelector(".delia-timeline")).toBeNull();
      expect(
        document.querySelector(".delpi-ui-conversation-reception"),
      ).toBeTruthy();
      expect(suggestionButtons().length).toBe(4);
    } finally {
      restore();
    }
  });

  it("never overwrites a non-empty draft — light note instead (SS-F04)", async () => {
    const { restore } = renderDemoApp();
    try {
      const input = screen.getByRole("textbox", {
        name: "Pergunte à DÉLIA",
      }) as HTMLTextAreaElement;
      fireEvent.change(input, { target: { value: "rascunho existente" } });

      fireEvent.click(suggestionButtons()[0]);
      expect(input.value).toBe("rascunho existente");
      const note = document.querySelector(
        ".delpi-ui-starter-suggestions__note",
      );
      expect(note?.getAttribute("role")).toBe("status");
      expect(note?.textContent).toContain("apague o texto atual");

      // The note clears as soon as the user edits the draft.
      fireEvent.change(input, { target: { value: "" } });
      expect(
        document.querySelector(".delpi-ui-starter-suggestions__note"),
      ).toBeNull();
    } finally {
      restore();
    }
  });

  it("a repeated click after a successful selection cannot duplicate text", async () => {
    const { restore } = renderDemoApp();
    try {
      const input = screen.getByRole("textbox", {
        name: "Pergunte à DÉLIA",
      }) as HTMLTextAreaElement;

      fireEvent.click(suggestionButtons()[0]);
      await waitFor(() =>
        expect(input.value).toBe(DELIA_STARTER_SUGGESTIONS[0].draftText),
      );
      fireEvent.click(suggestionButtons()[0]);
      // Draft unchanged — the second click hit the fail-safe note path.
      expect(input.value).toBe(DELIA_STARTER_SUGGESTIONS[0].draftText);
      expect(
        document.querySelector(".delpi-ui-starter-suggestions__note"),
      ).toBeTruthy();
    } finally {
      restore();
    }
  });

  it("suggestions are part of the reception flow — before the composer", () => {
    const { container, restore } = renderDemoApp();
    try {
      const reception = container.querySelector(
        ".delpi-ui-conversation-reception",
      );
      const suggestions = container.querySelector(SUGGESTIONS_SECTION);
      const composer = container.querySelector(".delia-composer-stack");
      expect(reception).toBeTruthy();
      expect(suggestions).toBeTruthy();
      expect(composer).toBeTruthy();
      expect(
        reception!.compareDocumentPosition(suggestions!) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      expect(
        suggestions!.compareDocumentPosition(composer!) &
          Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
    } finally {
      restore();
    }
  });
});
