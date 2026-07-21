import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditorClipboard } from "./useComunicadoEditorClipboard";

function fakeBlock(id: string): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: `block-${id}`,
    frame: { x: 10, y: 10, w: 20, h: 10 },
  };
}

describe("useComunicadoEditorClipboard", () => {
  it("ao colar, atualiza blocos antes de selecionar (ids novos no configRef)", async () => {
    const existing = [fakeBlock("existing")];
    let committed: ComunicadoBlock[] = existing;
    const order: string[] = [];

    const { result } = renderHook(() =>
      useComunicadoEditorClipboard({
        playlistId: "pl-1",
        getSources: () => [existing[0]],
        getExistingBlocks: () => committed,
        selectBlocksByIds: (ids) => {
          order.push("select");
          for (const id of ids) {
            expect(committed.some((block) => block.id === id)).toBe(true);
          }
        },
        updateBlocks: (blocks) => {
          order.push("update");
          committed = blocks;
        },
        removeSelected: () => undefined,
      }),
    );

    act(() => {
      result.current.copySelected();
    });

    await act(async () => {
      await result.current.pasteSelected();
    });

    expect(order).toEqual(["update", "select"]);
    expect(committed.length).toBe(2);
  });
});
