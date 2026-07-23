import { describe, expect, it } from "vitest";

import {
  resolveContextMenuIconPickerTargetId,
  shouldCancelTapDeselectOnContextMenu,
} from "./contextMenuSelectionGuard";

describe("contextMenuSelectionGuard", () => {
  it("cancela tap-deselect ao abrir menu (bloco ou fundo)", () => {
    expect(shouldCancelTapDeselectOnContextMenu("block")).toBe(true);
    expect(shouldCancelTapDeselectOnContextMenu("empty")).toBe(true);
  });

  it("resolve alvo do picker de ícone mesmo após fechar o menu", () => {
    expect(
      resolveContextMenuIconPickerTargetId({
        menuSelectedId: "icon-1",
        menuSelectedType: "icon",
        targetBlockId: "icon-1",
        targetBlockType: "icon",
      }),
    ).toBe("icon-1");

    expect(
      resolveContextMenuIconPickerTargetId({
        menuSelectedId: "shape-1",
        menuSelectedType: "shape",
        targetBlockId: "icon-2",
        targetBlockType: "icon",
      }),
    ).toBe("icon-2");

    expect(
      resolveContextMenuIconPickerTargetId({
        fallbackSelectedIds: ["icon-3"],
      }),
    ).toBe("icon-3");

    expect(resolveContextMenuIconPickerTargetId({})).toBeNull();
  });
});
