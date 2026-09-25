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

    configRef.current = snapshotConfig(v2);
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

    configRef.current = snapshotConfig(v2);
    act(() => {
      result.current.undo();
    });
    expect(deckHistory.undo).not.toHaveBeenCalled();
    expect(applyConfig).toHaveBeenLastCalledWith(v1Snap);
    expect(result.current.canRedo).toBe(true);
  });

  it("aplica runtime-only ack mesmo quando authoring já foi aplicado otimisticamente", () => {
    const applyConfig = vi.fn();
    const staleRuntime = emptyConfig([
      {
        id: "heading-1",
        type: "heading",
        frame: { x: 0, y: 0, w: 50, h: 10 },
        content: "REALIZADO 2025 X 2026",
        contentRuns: [{ text: "REALIZADO 2025 X 2026" }],
        style: { textCase: "lower" },
        resolved: {
          serverDisplayApplied: true,
          displayText: "REALIZADO 2025 X 2026",
          displayRuns: [{ text: "REALIZADO 2025 X 2026" }],
        },
      } as never,
    ]);
    const canonicalAck = emptyConfig([
      {
        id: "heading-1",
        type: "heading",
        frame: { x: 0, y: 0, w: 50, h: 10 },
        content: "REALIZADO 2025 X 2026",
        contentRuns: [{ text: "REALIZADO 2025 X 2026" }],
        style: { textCase: "lower" },
        resolved: {
          serverDisplayApplied: true,
          displayText: "realizado 2025 x 2026",
          displayRuns: [{ text: "realizado 2025 x 2026" }],
        },
      } as never,
    ]);
    const configRef = { current: staleRuntime };

    const { result } = renderHook(() =>
      useComunicadoEditorHistory({
        configRef,
        applyConfig,
        deckHistory: null,
      }),
    );

    act(() => {
      result.current.commitWithHistory(canonicalAck);
    });

    expect(applyConfig).toHaveBeenCalledOnce();
    expect(applyConfig).toHaveBeenCalledWith(canonicalAck, { persist: false });
    expect(result.current.canUndo).toBe(false);
  });

  it("commit idêntico não empilha undo (saída de texto blur+cleanup)", () => {
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

    const v2 = emptyConfig([
      { id: "a", type: "text", frame: { x: 0, y: 0, w: 10, h: 10 }, content: "v2" } as never,
    ]);

    act(() => {
      result.current.commitWithHistory(v2);
    });
    configRef.current = snapshotConfig(v2);
    applyConfig.mockClear();

    act(() => {
      result.current.commitWithHistory(v2);
    });
    expect(applyConfig).not.toHaveBeenCalled();
    expect(result.current.canUndo).toBe(true);

    act(() => {
      result.current.undo();
    });
    expect(applyConfig).toHaveBeenCalledOnce();
    expect(applyConfig.mock.calls[0]![0]).toEqual(
      expect.objectContaining({
        blocks: [expect.objectContaining({ content: "v1" })],
      }),
    );
    expect(result.current.canUndo).toBe(false);
  });
});
