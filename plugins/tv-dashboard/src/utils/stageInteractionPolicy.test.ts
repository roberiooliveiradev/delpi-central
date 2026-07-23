import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  isInlineTextEditableBlock,
  resolveStageDblClickAction,
  shouldArmTapDeselectOnDragCurrent,
} from "./stageInteractionPolicy";

const groupedText: ComunicadoBlock = {
  id: "t1",
  type: "text",
  content: "Texto",
  frame: { x: 0, y: 0, w: 10, h: 10 },
  groupId: "g1",
};

const groupedIcon: ComunicadoBlock = {
  id: "i1",
  type: "icon",
  iconName: "Target",
  frame: { x: 0, y: 0, w: 10, h: 10 },
  groupId: "g1",
};

const groupedHeading: ComunicadoBlock = {
  id: "h1",
  type: "heading",
  content: "PROPÓSITO",
  frame: { x: 10, y: 0, w: 20, h: 10 },
  groupId: "g1",
};

const blocks = [groupedText, groupedIcon, groupedHeading];

describe("stageInteractionPolicy dblclick", () => {
  it("texto/título/shape → enter-text-edit mesmo dentro de grupo fechado", () => {
    const closedIds = ["t1", "i1", "h1"];
    expect(
      resolveStageDblClickAction({
        block: groupedText,
        blocks,
        selectedIds: closedIds,
      }),
    ).toEqual({ type: "enter-text-edit", blockId: "t1" });
    expect(
      resolveStageDblClickAction({
        block: groupedHeading,
        blocks,
        selectedIds: closedIds,
      }),
    ).toEqual({ type: "enter-text-edit", blockId: "h1" });
  });

  it("ícone em grupo → isolate-child", () => {
    expect(
      resolveStageDblClickAction({
        block: groupedIcon,
        blocks,
        selectedIds: ["t1", "i1", "h1"],
      }),
    ).toEqual({ type: "isolate-child", blockId: "i1" });
  });

  it("ícone já isolado → none", () => {
    expect(
      resolveStageDblClickAction({
        block: groupedIcon,
        blocks,
        selectedIds: ["i1"],
      }),
    ).toEqual({ type: "none" });
  });

  it("bloco sem grupo não-texto → none", () => {
    const solo: ComunicadoBlock = {
      id: "img",
      type: "image",
      frame: { x: 0, y: 0, w: 10, h: 10 },
    };
    expect(
      resolveStageDblClickAction({
        block: solo,
        blocks: [solo],
        selectedIds: ["img"],
      }),
    ).toEqual({ type: "none" });
  });

  it("isInlineTextEditableBlock cobre heading/text/shape", () => {
    expect(isInlineTextEditableBlock(groupedText)).toBe(true);
    expect(isInlineTextEditableBlock(groupedHeading)).toBe(true);
    expect(
      isInlineTextEditableBlock({
        id: "s",
        type: "shape",
        shape: "rect",
        frame: { x: 0, y: 0, w: 10, h: 10 },
      }),
    ).toBe(true);
    expect(isInlineTextEditableBlock(groupedIcon)).toBe(false);
  });

  it("shouldArmTapDeselectOnDragCurrent só para não-texto", () => {
    expect(shouldArmTapDeselectOnDragCurrent(groupedText)).toBe(false);
    expect(shouldArmTapDeselectOnDragCurrent(groupedIcon)).toBe(true);
  });
});
