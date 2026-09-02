import { describe, expect, it, vi } from "vitest";

import { collectAllFreightPages, FREIGHT_EXPORT_PAGE_SIZE } from "./freightExport";

describe("collectAllFreightPages", () => {
  it("walks every page until hasNext is false", async () => {
    const loadPage = vi
      .fn()
      .mockResolvedValueOnce({
        items: [{ id: 1 }, { id: 2 }],
        pagination: { hasNext: true, totalItems: 3 },
      })
      .mockResolvedValueOnce({
        items: [{ id: 3 }],
        pagination: { hasNext: false, totalItems: 3 },
      });

    const rows = await collectAllFreightPages<{ id: number }>(loadPage, 2);

    expect(rows.map((row) => row.id)).toEqual([1, 2, 3]);
    expect(loadPage).toHaveBeenCalledTimes(2);
    expect(loadPage).toHaveBeenNthCalledWith(1, 1, 2);
    expect(loadPage).toHaveBeenNthCalledWith(2, 2, 2);
  });

  it("stops when the collected count reaches totalItems", async () => {
    const loadPage = vi.fn().mockResolvedValue({
      items: [{ id: 1 }, { id: 2 }],
      pagination: { hasNext: true, totalItems: 2 },
    });

    const rows = await collectAllFreightPages<{ id: number }>(loadPage, 2);

    expect(rows).toHaveLength(2);
    expect(loadPage).toHaveBeenCalledTimes(1);
  });

  it("defaults to the BFF max page size", async () => {
    const loadPage = vi.fn().mockResolvedValue({
      items: [],
      pagination: { hasNext: false, totalItems: 0 },
    });

    await collectAllFreightPages(loadPage);

    expect(loadPage).toHaveBeenCalledWith(1, FREIGHT_EXPORT_PAGE_SIZE);
  });
});
