import { describe, expect, it } from "vitest";

import {
  formatShortcutKeys,
  getKeyboardShortcut,
  listKeyboardShortcutsByGroup,
  TV_KEYBOARD_SHORTCUTS,
} from "./keyboardShortcuts";

describe("keyboardShortcuts catalog", () => {
  it("tem ids únicos", () => {
    const ids = TV_KEYBOARD_SHORTCUTS.map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("resolve entradas por id", () => {
    expect(getKeyboardShortcut("undo")?.keys).toBe("Ctrl+Z");
    expect(getKeyboardShortcut("zoom-wheel")?.showAltTip).toBe(true);
    expect(getKeyboardShortcut("keytips")?.keys).toBe("F1…F8");
    expect(getKeyboardShortcut("show-tips")?.description).toMatch(/ligar\/desligar/i);
    expect(getKeyboardShortcut("context-menu")?.keys).toBe("Shift+F10");
    expect(getKeyboardShortcut("group")?.keys).toBe("Ctrl+G");
    expect(getKeyboardShortcut("ungroup")?.keys).toBe("Ctrl+Shift+G");
    expect(getKeyboardShortcut("missing")).toBeUndefined();
  });

  it("reconhece tecla Alt para toggle de balões", async () => {
    const { isAltKey } = await import("../context/KeyboardShortcutsTipsProvider");
    expect(isAltKey({ key: "Alt", code: "AltLeft" })).toBe(true);
    expect(isAltKey({ key: "a", code: "KeyA" })).toBe(false);
  });

  it("agrupa todas as entradas sem perder nenhuma", () => {
    const grouped = listKeyboardShortcutsByGroup();
    const flat = grouped.flatMap((group) => group.entries);
    expect(flat).toHaveLength(TV_KEYBOARD_SHORTCUTS.length);
    expect(grouped.map((group) => group.group)).toEqual([
      "edicao",
      "selecao",
      "palco",
      "apresentacao",
    ]);
  });

  it("formatShortcutKeys preserva Ctrl fora de Mac", () => {
    const original = navigator.platform;
    Object.defineProperty(navigator, "platform", { configurable: true, value: "Win32" });
    expect(formatShortcutKeys("Ctrl+Z")).toBe("Ctrl+Z");
    Object.defineProperty(navigator, "platform", { configurable: true, value: original });
  });
});
