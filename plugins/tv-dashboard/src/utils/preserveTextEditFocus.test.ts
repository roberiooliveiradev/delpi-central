import { describe, expect, it } from "vitest";

import {
  PRESERVE_TEXT_EDIT_FOCUS_ATTR,
  shouldPreserveTextEditOnBlur,
} from "./preserveTextEditFocus";

describe("preserveTextEditFocus", () => {
  it("reconhece alvo com data-attr (botão da ribbon)", () => {
    const button = document.createElement("button");
    button.setAttribute(PRESERVE_TEXT_EDIT_FOCUS_ATTR, "");
    expect(shouldPreserveTextEditOnBlur(button)).toBe(true);
  });

  it("reconhece descendente dentro de wrapper com o attr", () => {
    const wrap = document.createElement("span");
    wrap.setAttribute(PRESERVE_TEXT_EDIT_FOCUS_ATTR, "");
    const inner = document.createElement("svg");
    wrap.appendChild(inner);
    expect(shouldPreserveTextEditOnBlur(inner)).toBe(true);
  });

  it("ignora alvo sem o attr", () => {
    const div = document.createElement("div");
    expect(shouldPreserveTextEditOnBlur(div)).toBe(false);
    expect(shouldPreserveTextEditOnBlur(null)).toBe(false);
  });
});
