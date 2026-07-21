import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditorClipboard } from "./useComunicadoEditorClipboard";
import { serializeInternalBlocksPayload } from "../../utils/externalClipboardPaste";

function fakeBlock(id: string, content = `block-${id}`): ComunicadoBlock {
  return {
    id,
    type: "text",
    content,
    frame: { x: 10, y: 10, w: 20, h: 10 },
  };
}

function mockDataTransfer(parts: { plain?: string; html?: string; files?: File[] }): DataTransfer {
  const files = parts.files ?? [];
  return {
    getData: (type: string) => {
      if (type === "text/plain") return parts.plain ?? "";
      if (type === "text/html") return parts.html ?? "";
      return "";
    },
    files: files as unknown as FileList,
    items: [] as unknown as DataTransferItemList,
  } as DataTransfer;
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

  it("não cola a última forma do plugin quando o SO trouxe HTML externo (Google)", async () => {
    const poliana = fakeBlock("poliana", "Poliana");
    let committed: ComunicadoBlock[] = [poliana];

    const { result } = renderHook(() =>
      useComunicadoEditorClipboard({
        playlistId: "pl-1",
        getSources: () => [poliana],
        getExistingBlocks: () => committed,
        selectBlocksByIds: () => undefined,
        updateBlocks: (blocks) => {
          committed = blocks;
        },
        removeSelected: () => undefined,
      }),
    );

    act(() => {
      result.current.copySelected();
    });
    expect(result.current.clipboardRef.current).toHaveLength(1);

    // HTML do Slides sem texto/imagem no evento — planner vazio, mas é externo.
    const applied = await act(async () =>
      result.current.pasteFromClipboardData(
        mockDataTransfer({
          html: `<html><body><div class="punch-viewer"><svg></svg></div></body></html>`,
          plain: "",
        }),
        { allowInternalFallback: true },
      ),
    );

    expect(applied).toBe(false);
    expect(committed).toHaveLength(1);
    expect(committed[0].content).toBe("Poliana");
  });

  it("cola texto externo do SO em vez do clipboard interno", async () => {
    const poliana = fakeBlock("poliana", "Poliana");
    let committed: ComunicadoBlock[] = [poliana];

    const { result } = renderHook(() =>
      useComunicadoEditorClipboard({
        playlistId: "pl-1",
        getSources: () => [poliana],
        getExistingBlocks: () => committed,
        selectBlocksByIds: () => undefined,
        updateBlocks: (blocks) => {
          committed = blocks;
        },
        removeSelected: () => undefined,
      }),
    );

    act(() => {
      result.current.copySelected();
    });

    await act(async () => {
      await result.current.pasteFromClipboardData(
        mockDataTransfer({ plain: "PROPÓSITO — Transformar conexões" }),
        { allowInternalFallback: true },
      );
    });

    expect(committed.length).toBe(2);
    expect(committed.some((block) => String(block.content ?? "").includes("PROPÓSITO"))).toBe(true);
    expect(committed.filter((block) => block.content === "Poliana")).toHaveLength(1);
  });

  it("ainda cola da memória quando o SO está vazio", async () => {
    const poliana = fakeBlock("poliana", "Poliana");
    let committed: ComunicadoBlock[] = [poliana];

    const { result } = renderHook(() =>
      useComunicadoEditorClipboard({
        playlistId: "pl-1",
        getSources: () => [poliana],
        getExistingBlocks: () => committed,
        selectBlocksByIds: () => undefined,
        updateBlocks: (blocks) => {
          committed = blocks;
        },
        removeSelected: () => undefined,
      }),
    );

    act(() => {
      result.current.copySelected();
    });

    await act(async () => {
      await result.current.pasteFromClipboardData(null, { allowInternalFallback: true });
    });

    expect(committed.length).toBe(2);
  });

  it("payload Delpi no SO continua tendo prioridade sobre HTML", async () => {
    const poliana = fakeBlock("poliana", "Poliana");
    let committed: ComunicadoBlock[] = [poliana];
    const internal = serializeInternalBlocksPayload([
      { ...fakeBlock("from-os", "Do SO"), type: "shape" } as ComunicadoBlock,
    ]);

    const { result } = renderHook(() =>
      useComunicadoEditorClipboard({
        playlistId: "pl-1",
        getSources: () => [poliana],
        getExistingBlocks: () => committed,
        selectBlocksByIds: () => undefined,
        updateBlocks: (blocks) => {
          committed = blocks;
        },
        removeSelected: () => undefined,
      }),
    );

    await act(async () => {
      await result.current.pasteFromClipboardData(
        mockDataTransfer({
          plain: internal,
          html: `<div style="background:#fff">Ignorar Google</div>`,
        }),
      );
    });

    expect(committed.some((block) => block.content === "Do SO")).toBe(true);
  });
});
