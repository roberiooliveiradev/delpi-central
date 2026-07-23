import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { snapshotConfig, useComunicadoEditorHistory } from "./useComunicadoEditorHistory";

function emptyConfig(blocks: ComunicadoConfig["blocks"] = []): ComunicadoConfig {
  return { blocks };
}

describe("useComunicadoEditorHistory", () => {
  it("undo/redo restaura configs locais sem deckHistory", () => {
    const applyConfig = vi.fn();
    const configRef = {
      current: emptyConfig([
        { id: "a", type: "text", frame: { x: 0, y: 0, w: 10, h: 10 }, content: "v1" } as never,
      ]),
    };

    const { result } = renderHook(() =>
      useComunicadoEditorHistory({
        configRef,
        applyConfig,
        deckHistory: null,
      }),
    );

    const v1Snap = snapshotConfig(configRef.current);
    const v2 = emptyConfig([
      { id: "a", type: "text", frame: { x: 0, y: 0, w: 10, h: 10 }, content: "v2" } as never,
    ]);

    act(() => {
      result.current.commitWithHistory(v2);
    });
    expect(applyConfig).toHaveBeenLastCalledWith(v2);
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);

    configRef.current = v2;
    act(() => {
      result.current.undo();
    });
    expect(applyConfig).toHaveBeenLastCalledWith(v1Snap);
    expect(result.current.canRedo).toBe(true);

    const v2Snap = snapshotConfig(v2);
    configRef.current = v1Snap;
    act(() => {
      result.current.redo();
    });
    expect(applyConfig).toHaveBeenLastCalledWith(v2Snap);
  });

  it("com deckHistory ainda empilha undo local imediato (não espera save)", () => {
    const applyConfig = vi.fn();
    const deckHistory = {
      recordBeforeChange: vi.fn(),
      undo: vi.fn(),
      redo: vi.fn(),
      canUndo: false,
      canRedo: false,
      historyEpoch: 0,
      setLiveComunicadoConfig: vi.fn(),
    };
    const configRef = {
      current: emptyConfig([
        { id: "a", type: "text", frame: { x: 0, y: 0, w: 10, h: 10 }, content: "v1" } as never,
      ]),
    };

    const { result } = renderHook(() =>
      useComunicadoEditorHistory({
        configRef,
        applyConfig,
        deckHistory,
      }),
    );

    const v1Snap = snapshotConfig(configRef.current);
    const v2 = emptyConfig([
      { id: "a", type: "text", frame: { x: 0, y: 0, w: 10, h: 10 }, content: "v2" } as never,
    ]);

    act(() => {
      result.current.commitWithHistory(v2);
    });
    expect(deckHistory.recordBeforeChange).toHaveBeenCalledOnce();
    expect(result.current.canUndo).toBe(true);

    configRef.current = v2;
    act(() => {
      result.current.undo();
    });
    expect(deckHistory.undo).not.toHaveBeenCalled();
    expect(applyConfig).toHaveBeenLastCalledWith(v1Snap);
    expect(result.current.canRedo).toBe(true);
  });
});
