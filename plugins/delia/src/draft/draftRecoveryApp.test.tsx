import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "../App";

afterEach(() => {
  cleanup();
});

function composer(): HTMLTextAreaElement {
  return screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement;
}

function undoButton(): HTMLElement {
  return screen.getByRole("button", {
    name: "Desfazer limpeza do rascunho",
  });
}

function queryUndoButton(): HTMLElement | null {
  return screen.queryByRole("button", {
    name: "Desfazer limpeza do rascunho",
  });
}

describe("ConversationDraftRecovery (doc 102 §9 — App integration)", () => {
  it("clear → toolbar undo icon restores the exact draft without submitting", () => {
    render(<App />);
    const field = composer();
    const draft = "primeira linha\nsegunda linha — çã é ✓";
    fireEvent.change(field, { target: { value: draft } });

    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    expect(field.value).toBe("");
    expect(undoButton()).toBeTruthy();
    expect(screen.queryByText("Rascunho limpo")).toBeNull();

    fireEvent.click(undoButton());
    expect(field.value).toBe(draft);
    expect(queryUndoButton()).toBeNull();
    // No turn was created by clear or undo.
    expect(
      screen.queryByText(draft.split("\n")[0]!, { selector: ".delia-turn" }),
    ).toBeNull();
  });

  it("clear on an empty draft is impossible — no undo affordance", () => {
    render(<App />);
    expect(
      screen.queryByRole("button", { name: "Limpar texto" }),
    ).toBeNull();
    expect(queryUndoButton()).toBeNull();
  });

  it("new text after clearing invalidates the candidate — undo never overwrites it", () => {
    render(<App />);
    const field = composer();
    fireEvent.change(field, { target: { value: "rascunho original" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    expect(undoButton()).toBeTruthy();

    fireEvent.change(field, { target: { value: "novo texto" } });
    expect(queryUndoButton()).toBeNull();
    expect(field.value).toBe("novo texto");
  });

  it("the undo icon renders inside the composer toolbar as a polite status", () => {
    render(<App />);
    fireEvent.change(composer(), { target: { value: "algo" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));

    const undo = undoButton();
    expect(undo.closest(".delpi-ui-message-composer__toolbar")).toBeTruthy();
    const status = screen
      .getAllByRole("status")
      .find((el) => el.contains(undo));
    expect(status).toBeTruthy();
  });

  it("a second clear replaces the first candidate — undo restores the latest only", () => {
    render(<App />);
    const field = composer();
    fireEvent.change(field, { target: { value: "primeiro" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    fireEvent.change(field, { target: { value: "segundo" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    fireEvent.click(undoButton());
    expect(field.value).toBe("segundo");
    expect(queryUndoButton()).toBeNull();
  });
});
