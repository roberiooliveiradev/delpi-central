import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  cloneBlocksForClipboard,
  detachClipboardGroupIds,
  pasteClipboardBlocks,
} from "../../utils/comunicadoEditorClipboard";

function fakeBlock(id: string, groupId?: string): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: `block-${id}`,
    frame: { x: 10, y: 10, w: 20, h: 10 },
    ...(groupId ? { groupId } : {}),
  };
}

describe("comunicadoEditorClipboard", () => {
  it("clona blocos preservando conteúdo", () => {
    const cloned = cloneBlocksForClipboard([fakeBlock("a"), fakeBlock("b")]);
    expect(cloned).toHaveLength(2);
    expect(cloned[0].id).toBe("a");
    expect(cloned[1].content).toBe("block-b");
  });

  it("cola com novos ids e offset de frame", () => {
    const payload = cloneBlocksForClipboard([fakeBlock("a")]);
    const result = pasteClipboardBlocks([fakeBlock("existing")], payload, { x: 2, y: 2 });
    expect(result.blocks.length).toBe(2);
    expect(result.pastedIds).toHaveLength(1);
    expect(result.pastedIds[0]).not.toBe("a");
  });

  it("cola grupo desagrupado (sem groupId nas cópias)", () => {
    const payload = cloneBlocksForClipboard([
      fakeBlock("a", "grp_src"),
      fakeBlock("b", "grp_src"),
    ]);
    expect(payload.every((block) => block.groupId === "grp_src")).toBe(true);
    expect(detachClipboardGroupIds(payload).every((block) => !block.groupId)).toBe(true);

    const existing = [fakeBlock("existing", "grp_src")];
    const result = pasteClipboardBlocks(existing, payload, { x: 2, y: 2 });
    const pasted = result.blocks.filter((block) => result.pastedIds.includes(block.id));
    expect(pasted).toHaveLength(2);
    expect(pasted.every((block) => !block.groupId)).toBe(true);
    expect(existing[0].groupId).toBe("grp_src");
  });
});
