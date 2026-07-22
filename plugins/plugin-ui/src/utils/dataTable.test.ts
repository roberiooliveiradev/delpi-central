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

  it("usa sortValue quando render devolve nó React (ex.: badge)", () => {
    const text = buildDataTableSearchText(
      { work_center: "CT-70", work_center_name: "INSPEÇÃO FINAL" },
      [
        {
          render: () => ({ $$typeof: Symbol.for("react.element") }),
          sortValue: (row) => row.work_center,
        },
        {
          render: (row) => row.work_center_name,
        },
      ],
    );
    expect(text).toContain("ct-70");
    expect(text).toContain("inspeção final");
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
