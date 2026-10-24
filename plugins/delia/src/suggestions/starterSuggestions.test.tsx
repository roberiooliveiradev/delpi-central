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

describe("resolveStarterSuggestions — default list (doc 93 §16, F02-A-R1)", () => {
  it("returns the frozen four default questions to every admitted user", () => {
    const items = resolveStarterSuggestions();
    expect(items).toBe(DELIA_STARTER_SUGGESTIONS);
    expect(items).toHaveLength(4);
  });

  it("fixtures are honest questions with editable draft text, no capability ids", () => {
    for (const item of DELIA_STARTER_SUGGESTIONS) {
      expect(item.draftText.endsWith("?")).toBe(true);
      expect(item.id).not.toMatch(/mcp|tool|provider|permission/i);
      expect(item.draftText.length).toBeLessThan(200);
    }
  });
});

describe("App — starter suggestions integration (F02-A-R1)", () => {
  it("renders the four cards on the empty reception with no demo param", () => {
    const { container } = render(<App />);
    expect(container.querySelector(SUGGESTIONS_SECTION)).toBeTruthy();
    expect(suggestionButtons()).toHaveLength(4);
    expect(document.body.textContent).toContain(
      "Explore algumas possibilidades para começar",
    );
    // Production path — no ?delia-demo banner, no QA admission needed.
    expect(document.body.textContent).not.toContain(
      "Modo demonstração",
    );
  });

  it("hides the suggestions once a turn exists", async () => {
    const previousUrl = window.location.href;
    window.history.replaceState(null, "", "/apps/delia?delia-demo=simple");
    try {
      const { container } = render(<App />);
      const input = screen.getByRole("textbox", {
        name: "Pergunte à DÉLIA",
      });
      fireEvent.change(input, { target: { value: "pergunta qualquer" } });
      fireEvent.click(screen.getByRole("button", { name: "Enviar mensagem" }));
      await waitFor(() =>
        expect(
          container.querySelector(SUGGESTIONS_SECTION),
        ).toBeNull(),
      );
      expect(container.querySelector(".delia-timeline")).toBeTruthy();
    } finally {
      window.history.replaceState(null, "", previousUrl);
    }
  });

  it("selecting a card fills the draft, focuses the composer, never submits", async () => {
    render(<App />);
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
  });

  it("never overwrites a non-empty draft — light note instead (SS-F04)", async () => {
    render(<App />);
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
  });

  it("a repeated click after a successful selection cannot duplicate text", async () => {
    render(<App />);
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
  });

  it("suggestions are part of the reception flow — before the composer", () => {
    const { container } = render(<App />);
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
  });
});
