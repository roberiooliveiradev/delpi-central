import { act, renderHook } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it } from "vitest";
import type { ComunicadoBlock, ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditorSelection } from "./useComunicadoEditorSelection";

const blocks: ComunicadoBlock[] = [
  { id: "a", type: "text", content: "A", frame: { x: 0, y: 0, w: 10, h: 10 } },
  { id: "b", type: "text", content: "B", frame: { x: 0, y: 0, w: 10, h: 10 } },
];

describe("useComunicadoEditorSelection", () => {
  it("seleciona e limpa blocos", () => {
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks });
      const updateBlockTextFieldsRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks,
        updateBlockTextFieldsRef,
      });
    });

    expect(result.current.selectedIds).toEqual([]);

    act(() => {
      result.current.selectBlock("b");
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.clearSelection();
    });
    expect(result.current.selectedIds).toEqual([]);
  });

  it("troca de slide limpa seleção sem auto-selecionar bloco", () => {
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks });
      const updateBlockTextFieldsRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks,
        updateBlockTextFieldsRef,
      });
    });

    act(() => {
      result.current.selectBlock("b");
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.resetSelectionForSlide();
    });
    expect(result.current.selectedIds).toEqual([]);
  });

  it("additive (Shift) alterna ids na multi-seleção", () => {
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks });
      const updateBlockTextFieldsRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks,
        updateBlockTextFieldsRef,
      });
    });

    act(() => {
      result.current.selectBlock("a");
    });
    act(() => {
      result.current.selectBlock("b", { additive: true });
    });
    expect(result.current.selectedIds).toEqual(["a", "b"]);

    act(() => {
      result.current.selectBlock("a", { additive: true });
    });
    expect(result.current.selectedIds).toEqual(["b"]);
  });

  it("selectBlocksByIds substitui a seleção (marquee)", () => {
    const { result } = renderHook(() => {
      const configRef = useRef<ComunicadoConfig>({ version: 2, blocks });
      const updateBlockTextFieldsRef = useRef(() => {});
      return useComunicadoEditorSelection({
        configRef,
        blocks,
        updateBlockTextFieldsRef,
      });
    });

    act(() => {
      result.current.selectBlock("a");
    });
    act(() => {
      result.current.selectBlocksByIds(["a", "b"]);
    });
    expect(result.current.selectedIds).toEqual(["a", "b"]);
  });
});
