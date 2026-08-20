import { describe, expect, it, vi } from "vitest";
import { createRef } from "react";
import { render, screen, fireEvent } from "@testing-library/react";

import { EmojiInsertMenu, emojiInsertMenuBemClasses } from "./EmojiInsertMenu";
import { EMOJI_CATALOG, getEmojiCatalog } from "../../content/emojiCatalog";

describe("emojiCatalog", () => {
  it("expõe cerca de 40 emojis com id, glyph e label", () => {
    const items = getEmojiCatalog();
    expect(items.length).toBeGreaterThanOrEqual(40);
    expect(items.length).toBeLessThanOrEqual(50);
    expect(items).toBe(EMOJI_CATALOG);
    for (const item of items) {
      expect(item.id).toBeTruthy();
      expect(item.glyph).toBeTruthy();
      expect(item.label).toBeTruthy();
    }
  });
});

describe("EmojiInsertMenu", () => {
  it("seleciona emoji e fecha o painel", () => {
    const onSelect = vi.fn();
    const onOpenChange = vi.fn();
    const anchorRef = createRef<HTMLButtonElement>();
    const classNames = emojiInsertMenuBemClasses("cm");

    render(
      <>
        <button ref={anchorRef} type="button">
          anchor
        </button>
        <EmojiInsertMenu
          open
          onOpenChange={onOpenChange}
          anchorRef={anchorRef}
          onSelect={onSelect}
          classNames={classNames}
          listAriaLabel="Inserir emoji"
          items={EMOJI_CATALOG.slice(0, 3)}
        />
      </>,
    );

    expect(screen.getByRole("dialog", { name: "Inserir emoji" })).toBeTruthy();
    fireEvent.mouseDown(screen.getByRole("option", { name: EMOJI_CATALOG[0]!.label }));
    expect(onSelect).toHaveBeenCalledWith(EMOJI_CATALOG[0]);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
