import { describe, expect, it } from "vitest";

import { INTERACTION_ROOMS_CONTENT, formatInteractionRoomContextSubtitle } from "./interactionRoomsContent";

describe("INTERACTION_ROOMS_CONTENT", () => {
  it("usa Neste chat no título e no ícone do painel", () => {
    expect(INTERACTION_ROOMS_CONTENT.contextToggle).toBe("Neste chat");
    expect(INTERACTION_ROOMS_CONTENT.inboxToolbarTitle).toBe("Conversas");
    expect(INTERACTION_ROOMS_CONTENT.formatFontSizeAriaLabel).toBe("Tamanho da fonte");
    expect(INTERACTION_ROOMS_CONTENT.formatUndoAriaLabel).toBe("Desfazer");
    expect(INTERACTION_ROOMS_CONTENT.formatRedoAriaLabel).toBe("Refazer");
    expect(INTERACTION_ROOMS_CONTENT.formatUnderlineAriaLabel).toBe("Sublinhado");
  });
});

describe("formatInteractionRoomContextSubtitle", () => {
  it("junta chave, participantes e pins", () => {
    expect(formatInteractionRoomContextSubtitle("02|002573", 2, 1)).toBe(
      "02|002573 · 2 participantes · 1 fixada",
    );
  });

  it("omite partes vazias", () => {
    expect(formatInteractionRoomContextSubtitle("  ", 0, 0)).toBe("");
    expect(formatInteractionRoomContextSubtitle(null, 3, 0)).toBe("3 participantes");
  });
});
