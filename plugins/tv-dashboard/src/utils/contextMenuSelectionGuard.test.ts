import { describe, expect, it } from "vitest";

import {
  resolveContextMenuIconPickerTargetId,
  resolveContextMenuSessionSelectedIds,
  sameSelectedIdSet,
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

  it("preserva seleção completa do grupo quando o alvo já está selecionado", () => {
    expect(
      resolveContextMenuSessionSelectedIds({
        selectedIds: ["a", "b"],
        targetBlockId: "a",
        blocks: [
          { id: "a", groupId: "g1" },
          { id: "b", groupId: "g1" },
        ],
      }),
    ).toEqual(["a", "b"]);
  });

  it("não colapsa para o target quando a seleção inclui o alvo", () => {
    expect(
      resolveContextMenuSessionSelectedIds({
        selectedIds: ["a", "b", "c"],
        targetBlockId: "b",
        blocks: [{ id: "a" }, { id: "b" }, { id: "c" }],
      }),
    ).toEqual(["a", "b", "c"]);
  });

  it("expande grupo quando right-click em membro fora da seleção", () => {
    expect(
      resolveContextMenuSessionSelectedIds({
        selectedIds: [],
        targetBlockId: "a",
        blocks: [
          { id: "a", groupId: "g1" },
          { id: "b", groupId: "g1" },
        ],
      }).sort(),
    ).toEqual(["a", "b"]);
  });

  it("sameSelectedIdSet ignora ordem", () => {
    expect(sameSelectedIdSet(["a", "b"], ["b", "a"])).toBe(true);
    expect(sameSelectedIdSet(["a"], ["a", "b"])).toBe(false);
  });
});
