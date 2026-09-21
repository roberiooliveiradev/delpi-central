import { describe, expect, it } from "vitest";

import { helpdeskListPaginationBounds } from "./listPagination";

describe("helpdeskListPaginationBounds", () => {
  it("habilita próxima página só com has_more", () => {
    expect(
      helpdeskListPaginationBounds({ page: 1, pageSize: 20, itemCount: 20, hasMore: true }),
    ).toEqual({ total: 21, totalPages: 2 });
    expect(
      helpdeskListPaginationBounds({ page: 1, pageSize: 20, itemCount: 5, hasMore: false }),
    ).toEqual({ total: 5, totalPages: 1 });
  });

  it("mantém paginação em página vazia posterior", () => {
    expect(
      helpdeskListPaginationBounds({ page: 2, pageSize: 20, itemCount: 0, hasMore: false }),
    ).toEqual({ total: 20, totalPages: 2 });
  });

  it("zera total na primeira página sem itens", () => {
    expect(
      helpdeskListPaginationBounds({ page: 1, pageSize: 20, itemCount: 0, hasMore: false }),
    ).toEqual({ total: 0, totalPages: 1 });
  });
});
