import { describe, expect, it } from "vitest";

import {
  DECK_TAB_KEYTIPS,
  activateDeckKeyTipTarget,
  isDeckKeyTipActionKey,
  normalizeKeyTipLetter,
} from "./deckKeyTips";

describe("deckKeyTips", () => {
  it("normaliza letras e dígitos", () => {
    expect(normalizeKeyTipLetter("p")).toBe("P");
    expect(normalizeKeyTipLetter("1")).toBe("1");
  });

  it("letras das abas são únicas", () => {
    const letters = Object.values(DECK_TAB_KEYTIPS);
    expect(new Set(letters).size).toBe(letters.length);
  });

  it("reconhece tecla de ação KeyTip", () => {
    expect(
      isDeckKeyTipActionKey({
        key: "n",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
      } as KeyboardEvent),
    ).toBe(true);
    expect(
      isDeckKeyTipActionKey({
        key: "N",
        ctrlKey: true,
        metaKey: false,
        altKey: false,
      } as KeyboardEvent),
    ).toBe(false);
  });

  it("activateDeckKeyTipTarget clica no botão anotado", () => {
    const host = document.createElement("span");
    host.dataset.tdKeytipScope = "actions";
    host.dataset.tdKeytip = "N";
    const button = document.createElement("button");
    let clicked = false;
    button.addEventListener("click", () => {
      clicked = true;
    });
    host.appendChild(button);
    document.body.appendChild(host);
    try {
      expect(activateDeckKeyTipTarget("actions", "n")).toBe(true);
      expect(clicked).toBe(true);
    } finally {
      host.remove();
    }
  });
});
