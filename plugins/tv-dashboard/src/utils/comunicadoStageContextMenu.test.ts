import { createBlock, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { describe, expect, it } from "vitest";

import { cloneBlocksForClipboard, pasteClipboardBlocks } from "./comunicadoEditorClipboard";
import { groupBlocks } from "./comunicadoGrouping";
import { bringForward, bringToFront, sendBackward, sendToBack } from "./comunicadoLayerOrder";
import {
  isContextMenuActionEnabled,
  resolveContextMenuActionState,
} from "./comunicadoStageContextMenuActions";

describe("comunicadoEditorClipboard", () => {
  it("cola blocos com novos ids e deslocamento", () => {
    const source = createBlock("text", "Olá");
    source.frame = { x: 10, y: 20, w: 30, h: 10 };
    const { blocks, pastedIds } = pasteClipboardBlocks([], [source]);

    expect(blocks).toHaveLength(1);
    expect(pastedIds).toHaveLength(1);
    expect(blocks[0].id).not.toBe(source.id);
    expect(blocks[0].frame.x).toBe(12);
    expect(blocks[0].frame.y).toBe(22);
  });

  it("clona blocos sem metadados de preview", () => {
    const source = {
      ...createBlock("text", "Preview"),
      resolved: { value: 1 },
      url: "http://example.test/img.png",
    } as ComunicadoBlock & { resolved: unknown; url: string };

    const cloned = cloneBlocksForClipboard([source]);
    expect(cloned[0]).not.toHaveProperty("resolved");
    expect(cloned[0]).not.toHaveProperty("url");
    expect((cloned[0] as ComunicadoBlock & { content?: string }).content).toBe("Preview");
  });
});

describe("comunicadoLayerOrder", () => {
  function block(id: string, zIndex: number): ComunicadoBlock {
    const item = createBlock("text", id);
    item.id = id;
    item.style = { zIndex };
    return item;
  }

  it("traz seleção para frente preservando ordem relativa", () => {
    const blocks = [block("a", 1), block("b", 2), block("c", 3)];
    const next = bringToFront(blocks, ["a", "c"]);
    expect(next.map((item) => item.id)).toEqual(["b", "a", "c"]);
    expect(next.map((item) => item.style?.zIndex)).toEqual([1, 2, 3]);
  });

  it("envia seleção para trás", () => {
    const blocks = [block("a", 1), block("b", 2), block("c", 3)];
    const next = sendToBack(blocks, ["b"]);
    expect(next.map((item) => item.id)).toEqual(["b", "a", "c"]);
  });

  it("avança e recua uma camada", () => {
    const blocks = [block("a", 1), block("b", 2), block("c", 3)];
    expect(bringForward(blocks, ["a"]).map((item) => item.id)).toEqual(["b", "a", "c"]);
    expect(sendBackward(blocks, ["c"]).map((item) => item.id)).toEqual(["a", "c", "b"]);
  });
});

describe("comunicadoStageContextMenuActions", () => {
  it("habilita colar sem seleção quando há clipboard", () => {
    const state = resolveContextMenuActionState({ selected: null, canPaste: true });
    expect(isContextMenuActionEnabled("paste", state)).toBe(true);
    expect(isContextMenuActionEnabled("copy", state)).toBe(false);
  });

  it("habilita inserir no palco vazio e desabilita com seleção", () => {
    const empty = resolveContextMenuActionState({ selected: null, canPaste: false });
    expect(isContextMenuActionEnabled("insertText", empty)).toBe(true);
    expect(isContextMenuActionEnabled("insertShape", empty)).toBe(true);
    expect(isContextMenuActionEnabled("insertDataSource", empty)).toBe(true);

    const selected = createBlock("text", "Selecionado");
    const withSelection = resolveContextMenuActionState({ selected, canPaste: false });
    expect(isContextMenuActionEnabled("insertText", withSelection)).toBe(false);
  });

  it("habilita editar texto em blocos suportados", () => {
    const selected = createBlock("text", "Editável");
    const state = resolveContextMenuActionState({ selected, canPaste: false });
    expect(state.canEditText).toBe(true);
    expect(isContextMenuActionEnabled("editText", state)).toBe(true);
  });

  it("habilita duplicar/girar com seleção e agrupar/alinhar com multi", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const c = createBlock("text", "C");
    const blocks = [a, b, c];

    const single = resolveContextMenuActionState({
      selected: a,
      canPaste: false,
      selectedIds: [a.id],
      blocks,
    });
    expect(isContextMenuActionEnabled("duplicate", single)).toBe(true);
    expect(isContextMenuActionEnabled("rotateCw", single)).toBe(true);
    expect(isContextMenuActionEnabled("group", single)).toBe(false);
    expect(isContextMenuActionEnabled("align-left", single)).toBe(false);
    expect(isContextMenuActionEnabled("align-slide-left", single)).toBe(true);
    expect(isContextMenuActionEnabled("distribute-h", single)).toBe(false);
    expect(isContextMenuActionEnabled("editText", single)).toBe(true);

    const multi = resolveContextMenuActionState({
      selected: a,
      canPaste: false,
      selectedIds: [a.id, b.id],
      blocks,
    });
    expect(isContextMenuActionEnabled("group", multi)).toBe(true);
    expect(isContextMenuActionEnabled("align-left", multi)).toBe(true);
    expect(isContextMenuActionEnabled("distribute-h", multi)).toBe(false);
    expect(isContextMenuActionEnabled("editText", multi)).toBe(false);

    const three = resolveContextMenuActionState({
      selected: a,
      canPaste: false,
      selectedIds: [a.id, b.id, c.id],
      blocks,
    });
    expect(isContextMenuActionEnabled("distribute-v", three)).toBe(true);
  });

  it("habilita desagrupar e reagrupar conforme ribbon", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    const grouped = groupBlocks([a, b], [a.id, b.id], "grp_test");
    const withGroup = resolveContextMenuActionState({
      selected: grouped[0],
      canPaste: false,
      selectedIds: [a.id, b.id],
      blocks: grouped,
    });
    expect(isContextMenuActionEnabled("ungroup", withGroup)).toBe(true);
    expect(isContextMenuActionEnabled("regroup", withGroup)).toBe(false);

    const afterUngroup = resolveContextMenuActionState({
      selected: a,
      canPaste: false,
      selectedIds: [a.id],
      blocks: [a, b],
      lastUngroupedIds: [a.id, b.id],
    });
    expect(isContextMenuActionEnabled("ungroup", afterUngroup)).toBe(false);
    expect(isContextMenuActionEnabled("regroup", afterUngroup)).toBe(true);
  });
});
