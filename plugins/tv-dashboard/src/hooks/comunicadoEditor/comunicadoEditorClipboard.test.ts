import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  cloneBlocksForClipboard,
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

  it("cola grupo com novo groupId (cópia agrupada, fora do grupo da origem)", () => {
    const payload = cloneBlocksForClipboard([
      fakeBlock("a", "grp_src"),
      fakeBlock("b", "grp_src"),
    ]);
    const existing = [fakeBlock("existing", "grp_src")];
    const result = pasteClipboardBlocks(existing, payload, { x: 2, y: 2 });
    const pasted = result.blocks.filter((block) => result.pastedIds.includes(block.id));
    expect(pasted).toHaveLength(2);
    expect(pasted[0]?.groupId).toBeTruthy();
    expect(pasted[0]?.groupId).not.toBe("grp_src");
    expect(pasted[1]?.groupId).toBe(pasted[0]?.groupId);
    expect(existing[0].groupId).toBe("grp_src");
  });
});
