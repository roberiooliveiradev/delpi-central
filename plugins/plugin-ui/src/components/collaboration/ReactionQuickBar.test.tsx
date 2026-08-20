import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getQuickReactionCatalog,
  QUICK_REACTION_CATALOG,
} from "../../content/emojiCatalog";
import {
  ReactionQuickBar,
  reactionQuickBarBemClasses,
} from "./ReactionQuickBar";

const classNames = reactionQuickBarBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("getQuickReactionCatalog", () => {
  it("expõe exatamente 5 reações rápidas do catálogo", () => {
    const items = getQuickReactionCatalog();
    expect(items).toBe(QUICK_REACTION_CATALOG);
    expect(items).toHaveLength(5);
    for (const item of items) {
      expect(item.id).toBeTruthy();
      expect(item.glyph).toBeTruthy();
    }
  });
});

describe("ReactionQuickBar", () => {
  it("mostra 5 quick + mais e dispara onPick", () => {
    const onPick = vi.fn();
    render(
      <ReactionQuickBar
        classNames={classNames}
        listAriaLabel="Reações rápidas"
        addAriaLabel="Mais reações"
        emojiMenuAriaLabel="Catálogo"
        onPick={onPick}
      />,
    );

    const group = screen.getByRole("group", { name: "Reações rápidas" });
    expect(group.querySelectorAll("button")).toHaveLength(6);
    fireEvent.click(screen.getByRole("button", { name: QUICK_REACTION_CATALOG[0]!.label }));
    expect(onPick).toHaveBeenCalledWith(QUICK_REACTION_CATALOG[0]!.id);
  });
});
