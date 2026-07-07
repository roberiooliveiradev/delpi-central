import { describe, expect, it } from "vitest";

import { buildDataTableSearchText } from "./dataTableSearch";
import { useClientPagination } from "./useClientPagination";
import { renderHook, act } from "@testing-library/react";

describe("buildDataTableSearchText", () => {
  it("concatena valores string/número das colunas", () => {
    const text = buildDataTableSearchText({ id: 1 }, [
      { render: () => "Alpha" },
      { render: () => 42 },
    ]);
    expect(text).toBe("alpha 42");
  });
});

describe("useClientPagination", () => {
  it("pagina itens localmente", () => {
    const items = [1, 2, 3, 4, 5];
    const { result } = renderHook(() => useClientPagination(items, 2));

    expect(result.current.slice).toEqual([1, 2]);
    expect(result.current.total).toBe(5);

    act(() => {
      result.current.setPage(2);
    });

    expect(result.current.slice).toEqual([3, 4]);
  });
});
