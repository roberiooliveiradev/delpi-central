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

    expect(result.current.selectedIds).toEqual(["a"]);

    act(() => {
      result.current.selectBlock("b");
    });
    expect(result.current.selectedIds).toEqual(["b"]);

    act(() => {
      result.current.clearSelection();
    });
    expect(result.current.selectedIds).toEqual([]);
  });
});
