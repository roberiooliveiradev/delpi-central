import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "../App";

afterEach(() => {
  cleanup();
});

function composer(): HTMLTextAreaElement {
  return screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement;
}

describe("ConversationDraftRecovery (doc 102 — App integration)", () => {
  it("clear → Desfazer restores the exact draft without submitting", () => {
    render(<App />);
    const field = composer();
    const draft = "primeira linha\nsegunda linha — çã é ✓";
    fireEvent.change(field, { target: { value: draft } });

    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    expect(field.value).toBe("");
    expect(screen.getByText("Rascunho limpo")).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: "Desfazer limpeza do rascunho" }),
    );
    expect(field.value).toBe(draft);
    expect(screen.queryByText("Rascunho limpo")).toBeNull();
    // No turn was created by clear or undo.
    expect(screen.queryByText(draft.split("\n")[0]!, {
      selector: ".delia-turn",
    })).toBeNull();
  });

  it("clear on an empty draft is impossible — no notice affordance", () => {
    render(<App />);
    expect(
      screen.queryByRole("button", { name: "Limpar texto" }),
    ).toBeNull();
    expect(screen.queryByText("Rascunho limpo")).toBeNull();
  });

  it("new text after clearing invalidates the candidate — undo never overwrites it", () => {
    render(<App />);
    const field = composer();
    fireEvent.change(field, { target: { value: "rascunho original" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    expect(screen.getByText("Rascunho limpo")).toBeTruthy();

    fireEvent.change(field, { target: { value: "novo texto" } });
    expect(screen.queryByText("Rascunho limpo")).toBeNull();
    expect(field.value).toBe("novo texto");
  });

  it("the notice is a polite status region with a named undo action", () => {
    render(<App />);
    fireEvent.change(composer(), { target: { value: "algo" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));

    const status = screen.getAllByRole("status").find((el) =>
      el.textContent?.includes("Rascunho limpo"),
    );
    expect(status).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Desfazer limpeza do rascunho" }),
    ).toBeTruthy();
  });

  it("a second clear replaces the first candidate — undo restores the latest only", () => {
    render(<App />);
    const field = composer();
    fireEvent.change(field, { target: { value: "primeiro" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    fireEvent.change(field, { target: { value: "segundo" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar texto" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Desfazer limpeza do rascunho" }),
    );
    expect(field.value).toBe("segundo");
  });
});
