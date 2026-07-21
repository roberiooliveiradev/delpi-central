import { describe, expect, it } from "vitest";

import {
  DECK_TAB_KEYTIPS,
  activateDeckKeyTipTarget,
  isDeckKeyTipActionKey,
  isDeckKeyTipFunctionKey,
  normalizeKeyTipLetter,
} from "./deckKeyTips";

describe("deckKeyTips", () => {
  it("normaliza letras, dígitos e teclas F1…", () => {
    expect(normalizeKeyTipLetter("p")).toBe("P");
    expect(normalizeKeyTipLetter("1")).toBe("1");
    expect(normalizeKeyTipLetter("f1")).toBe("F1");
    expect(normalizeKeyTipLetter("F8")).toBe("F8");
  });

  it("atalhos de aba são F1… únicos na ordem das abas", () => {
    const tips = Object.values(DECK_TAB_KEYTIPS);
    expect(new Set(tips).size).toBe(tips.length);
    expect(DECK_TAB_KEYTIPS.insert).toBe("F1");
    expect(DECK_TAB_KEYTIPS.view).toBe("F2");
    expect(tips.every((tip) => /^F\d+$/.test(tip))).toBe(true);
    expect(DECK_TAB_KEYTIPS).not.toHaveProperty("home");
  });

  it("reconhece tecla de função e tecla de ação", () => {
    expect(
      isDeckKeyTipFunctionKey({
        key: "F1",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
        shiftKey: false,
      } as KeyboardEvent),
    ).toBe(true);
    expect(
      isDeckKeyTipFunctionKey({
        key: "F5",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
        shiftKey: true,
      } as KeyboardEvent),
    ).toBe(false);
    expect(
      isDeckKeyTipFunctionKey({
        key: "F12",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
        shiftKey: false,
      } as KeyboardEvent),
    ).toBe(false);
    expect(
      isDeckKeyTipFunctionKey({
        key: "F11",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
        shiftKey: false,
      } as KeyboardEvent),
    ).toBe(false);
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
        key: "F1",
        ctrlKey: false,
        metaKey: false,
        altKey: false,
      } as KeyboardEvent),
    ).toBe(false);
  });

  it("activateDeckKeyTipTarget clica no botão anotado (aba F1 e ação N)", () => {
    const tabHost = document.createElement("span");
    tabHost.dataset.tdKeytipScope = "tabs";
    tabHost.dataset.tdKeytip = "F1";
    const tabButton = document.createElement("button");
    let tabClicked = false;
    tabButton.addEventListener("click", () => {
      tabClicked = true;
    });
    tabHost.appendChild(tabButton);
    document.body.appendChild(tabHost);

    const actionHost = document.createElement("span");
    actionHost.dataset.tdKeytipScope = "actions";
    actionHost.dataset.tdKeytip = "N";
    const actionButton = document.createElement("button");
    let actionClicked = false;
    actionButton.addEventListener("click", () => {
      actionClicked = true;
    });
    actionHost.appendChild(actionButton);
    document.body.appendChild(actionHost);

    try {
      expect(activateDeckKeyTipTarget("tabs", "f1")).toBe(true);
      expect(tabClicked).toBe(true);
      expect(activateDeckKeyTipTarget("actions", "n")).toBe(true);
      expect(actionClicked).toBe(true);
    } finally {
      tabHost.remove();
      actionHost.remove();
    }
  });
});
