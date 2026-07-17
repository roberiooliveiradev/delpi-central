import { describe, expect, it } from "vitest";
import { mergeComunicadoDataPages, resolveComunicadoDataPageState } from "./dataPagination";

describe("dataPagination", () => {
  it("reconhece paginação no payload operacional", () => {
    expect(resolveComunicadoDataPageState({
      data: { page: 1, page_size: 30, total: 75, total_pages: 3 },
    })).toEqual({ page: 1, pageSize: 30, totalPages: 3, hasMore: true });
  });

  it("concatena linhas mantendo a paginação mais recente", () => {
    const merged = mergeComunicadoDataPages(
      {
        data: { page: 1, total_pages: 2 },
        table: { rows: [{ id: 1 }], columns: [{ key: "id", label: "ID" }] },
      },
      {
        data: { page: 2, total_pages: 2 },
        table: { rows: [{ id: 2 }], columns: [{ key: "id", label: "ID" }] },
      },
    );
    expect(merged.table?.rows).toEqual([{ id: 1 }, { id: 2 }]);
    expect(resolveComunicadoDataPageState(merged)?.hasMore).toBe(false);
  });
});
