import { describe, expect, it } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  isGroupChildrenSelection,
  isIsolatedGroupChildSelection,
} from "./comunicadoGrouping";
import {
  resolveBlockWrapChromeFlags,
  resolveEscapeHierarchyAction,
  resolveGroupedBlockPointerDownAction,
  resolveStageSelectionHierarchy,
  resolveTapWithoutDragSelectionAction,
} from "./stageGroupedSelection";

function block(
  id: string,
  patch: Partial<ComunicadoBlock> & { type?: ComunicadoBlock["type"] } = {},
): ComunicadoBlock {
  return {
    id,
    type: patch.type ?? "shape",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    ...patch,
  } as ComunicadoBlock;
}

describe("resolveStageSelectionHierarchy", () => {
  it("grupo fechado = seleção pai", () => {
    const blocks = [
      block("a", { groupId: "g1" }),
      block("b", { groupId: "g1" }),
    ];
    expect(
      resolveStageSelectionHierarchy({
        blocks,
        selectedIds: ["a", "b"],
      }),
    ).toEqual({ mode: "parent", unit: "group", blockIds: ["a", "b"] });
  });

  it("subset do grupo = filhos", () => {
    const blocks = [
      block("a", { groupId: "g1" }),
      block("b", { groupId: "g1" }),
      block("c", { groupId: "g1" }),
    ];
    expect(
      resolveStageSelectionHierarchy({
        blocks,
        selectedIds: ["a", "b"],
      }),
    ).toEqual({ mode: "children", unit: "group", blockIds: ["a", "b"] });
    expect(isGroupChildrenSelection(blocks, ["a", "b"])).toBe(true);
    expect(isIsolatedGroupChildSelection(blocks, ["a"])).toBe(true);
  });

  it("KPI sem parte = pai complexo; com value = filhos", () => {
    const blocks = [block("k", { type: "kpi_view" })];
    expect(
      resolveStageSelectionHierarchy({
        blocks,
        selectedIds: ["k"],
      }),
    ).toEqual({ mode: "parent", unit: "complex", blockIds: ["k"] });
    expect(
      resolveStageSelectionHierarchy({
        blocks,
        selectedIds: ["k"],
        selectedPart: { kind: "value" },
      }),
    ).toEqual({
      mode: "children",
      unit: "complex",
      blockIds: ["k"],
      partKinds: ["value"],
    });
  });

  it("KPI card (moldura) permanece pai", () => {
    const blocks = [block("k", { type: "kpi_view" })];
    expect(
      resolveStageSelectionHierarchy({
        blocks,
        selectedIds: ["k"],
        selectedPart: { kind: "card" },
      }),
    ).toEqual({ mode: "parent", unit: "complex", blockIds: ["k"] });
  });
});

describe("resolveBlockWrapChromeFlags", () => {
  it("desativa outline/handles do pai com filho complexo ativo", () => {
    const hierarchy = resolveStageSelectionHierarchy({
      blocks: [block("k", { type: "kpi_view" })],
      selectedIds: ["k"],
      selectedPart: { kind: "value" },
    });
    expect(
      resolveBlockWrapChromeFlags({
        hierarchy,
        blockId: "k",
        blockType: "kpi_view",
        isSelected: true,
        closedGroupActive: false,
        selectedPart: { kind: "value" },
      }),
    ).toEqual({
      showOutline: false,
      showHandles: false,
      mutedAsGroupMember: false,
      partChildrenActive: true,
    });
  });

  it("filho de grupo isolado mantém outline e handles", () => {
    const blocks = [block("a", { groupId: "g1" }), block("b", { groupId: "g1" })];
    const hierarchy = resolveStageSelectionHierarchy({
      blocks,
      selectedIds: ["a"],
    });
    expect(
      resolveBlockWrapChromeFlags({
        hierarchy,
        blockId: "a",
        blockType: "shape",
        isSelected: true,
        closedGroupActive: false,
        selectedPart: null,
      }),
    ).toEqual({
      showOutline: true,
      showHandles: true,
      mutedAsGroupMember: false,
      partChildrenActive: false,
    });
  });

  it("edição de texto mantém outline e handles de redimensionamento", () => {
    const hierarchy = resolveStageSelectionHierarchy({
      blocks: [block("t1", { type: "text" })],
      selectedIds: ["t1"],
    });
    expect(
      resolveBlockWrapChromeFlags({
        hierarchy,
        blockId: "t1",
        blockType: "text",
        isSelected: true,
        closedGroupActive: false,
        selectedPart: null,
      }),
    ).toEqual({
      showOutline: true,
      showHandles: true,
      mutedAsGroupMember: false,
      partChildrenActive: false,
    });
  });
});

describe("resolveEscapeHierarchyAction", () => {
  it("prioriza limpar partes", () => {
    expect(
      resolveEscapeHierarchyAction({
        blocks: [],
        selectedIds: ["k"],
        hasPartSelection: true,
      }),
    ).toEqual({ type: "clear-parts" });
  });

  it("filhos de grupo sobem para o pai", () => {
    const blocks = [
      block("a", { groupId: "g1" }),
      block("b", { groupId: "g1" }),
    ];
    expect(
      resolveEscapeHierarchyAction({
        blocks,
        selectedIds: ["a"],
        hasPartSelection: false,
      }),
    ).toEqual({ type: "select-ids", ids: ["a", "b"] });
  });

  it("seleção pai ou bloco limpa com Esc", () => {
    const blocks = [
      block("a", { groupId: "g1" }),
      block("b", { groupId: "g1" }),
    ];
    expect(
      resolveEscapeHierarchyAction({
        blocks,
        selectedIds: ["a", "b"],
        hasPartSelection: false,
      }),
    ).toEqual({ type: "clear-selection" });
    expect(
      resolveEscapeHierarchyAction({
        blocks: [block("x")],
        selectedIds: ["x"],
        hasPartSelection: false,
      }),
    ).toEqual({ type: "clear-selection" });
  });
});

describe("resolveTapWithoutDragSelectionAction", () => {
  it("só limpa no segundo toque em item já selecionado (não agrupado)", () => {
    expect(
      resolveTapWithoutDragSelectionAction({
        selectedIds: ["a"],
        targetBlockId: "a",
        wasAlreadySelected: false,
      }),
    ).toEqual({ type: "none" });
    expect(
      resolveTapWithoutDragSelectionAction({
        selectedIds: ["a"],
        targetBlockId: "a",
        wasAlreadySelected: true,
      }),
    ).toEqual({ type: "clear-selection" });
  });

  it("com grupo fechado, 2º toque isola o subitem em vez de limpar", () => {
    const blocks = [block("a", { groupId: "g1" }), block("b", { groupId: "g1" })];
    expect(
      resolveTapWithoutDragSelectionAction({
        blocks,
        selectedIds: ["a", "b"],
        targetBlockId: "a",
        wasAlreadySelected: true,
      }),
    ).toEqual({ type: "isolate-child", blockId: "a" });
  });
});

describe("resolveGroupedBlockPointerDownAction", () => {
  it("1º clique expande o grupo; 2º isola o filho; Shift multiplica grupos", () => {
    const blocks = [block("a", { groupId: "g1" }), block("b", { groupId: "g1" })];
    expect(
      resolveGroupedBlockPointerDownAction({
        block: blocks[0]!,
        blocks,
        selectedIds: [],
        shiftKey: false,
        ctrlOrMeta: false,
        altKey: false,
      }),
    ).toEqual({ type: "select-expand-group", blockId: "a" });

    expect(
      resolveGroupedBlockPointerDownAction({
        block: blocks[0]!,
        blocks,
        selectedIds: ["a", "b"],
        shiftKey: false,
        ctrlOrMeta: false,
        altKey: false,
      }),
    ).toEqual({ type: "isolate-child", blockId: "a" });

    /* Shift com outro grupo / fora do modo filhos → toggle do grupo fechado. */
    expect(
      resolveGroupedBlockPointerDownAction({
        block: blocks[1]!,
        blocks,
        selectedIds: ["x"],
        shiftKey: true,
        ctrlOrMeta: false,
        altKey: false,
      }),
    ).toEqual({ type: "toggle-group", blockId: "b" });

    /* Shift com grupo fechado selecionado → também toggle-group (não isola). */
    expect(
      resolveGroupedBlockPointerDownAction({
        block: blocks[0]!,
        blocks,
        selectedIds: ["a", "b"],
        shiftKey: true,
        ctrlOrMeta: false,
        altKey: false,
      }),
    ).toEqual({ type: "toggle-group", blockId: "a" });

    /* Já em modo filhos: Shift alterna irmãos. */
    expect(
      resolveGroupedBlockPointerDownAction({
        block: blocks[1]!,
        blocks,
        selectedIds: ["a"],
        shiftKey: true,
        ctrlOrMeta: false,
        altKey: false,
      }),
    ).toEqual({ type: "toggle-child", blockId: "b" });
  });
});
