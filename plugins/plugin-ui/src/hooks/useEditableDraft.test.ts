import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useEditableDraft } from "./useEditableDraft";

describe("useEditableDraft", () => {
  it("marca dirty só após alteração e limpa com markSaved/reset/replace", () => {
    const { result } = renderHook(() => useEditableDraft({ nome: "A" }));

    expect(result.current.dirty).toBe(false);

    act(() => {
      result.current.setValue({ nome: "B" });
    });
    expect(result.current.dirty).toBe(true);

    act(() => {
      result.current.reset();
    });
    expect(result.current.value).toEqual({ nome: "A" });
    expect(result.current.dirty).toBe(false);

    act(() => {
      result.current.setValue({ nome: "C" });
      result.current.markSaved();
    });
    expect(result.current.dirty).toBe(false);

    act(() => {
      result.current.replace({ nome: "D" });
    });
    expect(result.current.value).toEqual({ nome: "D" });
    expect(result.current.dirty).toBe(false);
  });
});
