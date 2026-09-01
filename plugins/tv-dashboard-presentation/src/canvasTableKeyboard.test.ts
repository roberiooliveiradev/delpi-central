import { describe, expect, it } from "vitest";

import { resolveCanvasTableKeyboardAction } from "./canvasTableKeyboard";

const base = { row: 1, col: 1, rows: 3, cols: 3 };

describe("resolveCanvasTableKeyboardAction", () => {
  it("em editar: setas movem o caret — não navegam", () => {
    for (const key of ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"]) {
      expect(
        resolveCanvasTableKeyboardAction({ ...base, key, mode: "edit" }),
        key,
      ).toEqual({ type: "editCaret" });
    }
  });

  it("em editar: Enter commit+desce; Escape cancela; Tab move", () => {
    expect(
      resolveCanvasTableKeyboardAction({ ...base, key: "Enter", mode: "edit" }),
    ).toEqual({ type: "commitMove", next: { row: 2, col: 1 } });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "Enter",
        ctrl: true,
        mode: "edit",
      }),
    ).toEqual({ type: "commitStay" });
    expect(
      resolveCanvasTableKeyboardAction({ ...base, key: "Escape", mode: "edit" }),
    ).toEqual({ type: "cancelEdit" });
    expect(
      resolveCanvasTableKeyboardAction({ ...base, key: "Tab", mode: "edit" }),
    ).toEqual({ type: "commitMove", next: { row: 1, col: 2 } });
  });

  it("em navegar: setas trocam de célula; F2 entra em editar", () => {
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "ArrowRight",
        mode: "navigate",
      }),
    ).toEqual({ type: "navigate", next: { row: 1, col: 2 }, range: false });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "ArrowLeft",
        shift: true,
        mode: "navigate",
      }),
    ).toEqual({ type: "navigate", next: { row: 1, col: 0 }, range: true });
    expect(
      resolveCanvasTableKeyboardAction({ ...base, key: "F2", mode: "navigate" }),
    ).toEqual({ type: "enterEdit" });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "a",
        mode: "navigate",
      }),
    ).toEqual({ type: "enterEdit" });
  });

  it("não sai da grade nos cantos", () => {
    expect(
      resolveCanvasTableKeyboardAction({
        row: 0,
        col: 0,
        rows: 2,
        cols: 2,
        key: "ArrowUp",
        mode: "navigate",
      }),
    ).toEqual({ type: "navigate", next: { row: 0, col: 0 }, range: false });
    expect(
      resolveCanvasTableKeyboardAction({
        row: 1,
        col: 1,
        rows: 2,
        cols: 2,
        key: "ArrowRight",
        mode: "navigate",
      }),
    ).toEqual({ type: "navigate", next: { row: 1, col: 1 }, range: false });
  });

  it("navegar: Delete limpa; Alt+Enter em editar insere newline", () => {
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "Delete",
        mode: "navigate",
      }),
    ).toEqual({ type: "clearContent" });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "Backspace",
        mode: "navigate",
      }),
    ).toEqual({ type: "clearContent" });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "Enter",
        alt: true,
        mode: "edit",
      }),
    ).toEqual({ type: "insertNewline" });
    expect(
      resolveCanvasTableKeyboardAction({
        ...base,
        key: "c",
        ctrl: true,
        mode: "navigate",
      }),
    ).toEqual({ type: "clipboard", op: "copy" });
  });
});
