// @vitest-environment jsdom

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  useMachineLoadSequenceHistory,
  type SequenceKey,
} from "./useMachineLoadSequenceHistory";

const SCOPE = "01|2026-02|2026-02|CT-01A";

const K1: SequenceKey[] = [{ production_order: "A", operation_code: "01" }];
const K2: SequenceKey[] = [{ production_order: "A", operation_code: "02" }];

function renderHistory() {
  return renderHook(() => useMachineLoadSequenceHistory(SCOPE));
}

describe("useMachineLoadSequenceHistory", () => {
  it("peekUndo espía o topo sem consumir a pilha", () => {
    const { result } = renderHistory();
    act(() => result.current.pushUndo(K1));

    const peeked = result.current.peekUndo();
    expect(peeked).toEqual(K1);
    // peek não pop — o topo continua disponível para o pop pós-confirmação
    expect(result.current.peekUndo()).toEqual(K1);
    expect(result.current.canUndo).toBe(true);
  });

  it("undo consome a entrada e a devolve", () => {
    const { result } = renderHistory();
    act(() => result.current.pushUndo(K1));

    let restored: SequenceKey[] | null = null;
    act(() => {
      restored = result.current.undo();
    });
    expect(restored).toEqual(K1);
    expect(result.current.canUndo).toBe(false);
    expect(result.current.peekUndo()).toBeNull();
  });

  it("peekRedo espía sem consumir; redo consome", () => {
    const { result } = renderHistory();
    act(() => result.current.pushUndo(K1));
    act(() => {
      result.current.undo();
      result.current.rememberForRedo(K2);
    });

    expect(result.current.peekRedo()).toEqual(K2);
    expect(result.current.peekRedo()).toEqual(K2);
    act(() => {
      expect(result.current.redo()).toEqual(K2);
    });
    expect(result.current.peekRedo()).toBeNull();
  });

  it("pushUndo limpa a pilha de redo", () => {
    const { result } = renderHistory();
    act(() => result.current.pushUndo(K1));
    act(() => {
      result.current.undo();
      result.current.rememberForRedo(K2);
      result.current.pushUndo(K2);
    });
    expect(result.current.canRedo).toBe(false);
    expect(result.current.peekRedo()).toBeNull();
  });

  it("reset zera as duas pilhas — caminho de falha/409 não deixa resíduo", () => {
    const { result } = renderHistory();
    act(() => result.current.pushUndo(K1));
    act(() => result.current.pushUndo(K2));
    act(() => result.current.reset());

    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(false);
    expect(result.current.peekUndo()).toBeNull();
    expect(result.current.peekRedo()).toBeNull();
  });

  it("mudança de escopo (CT/período) zera as pilhas", () => {
    const { result, rerender } = renderHook(
      ({ scope }) => useMachineLoadSequenceHistory(scope),
      { initialProps: { scope: SCOPE } },
    );
    act(() => result.current.pushUndo(K1));
    expect(result.current.canUndo).toBe(true);

    rerender({ scope: "01|2026-02|2026-02|CT-02" });
    expect(result.current.canUndo).toBe(false);
    expect(result.current.peekUndo()).toBeNull();
  });
});
