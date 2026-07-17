import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getPlaylistHistorySnapshot,
  listPlaylistHistory,
  restorePlaylistHistorySnapshot,
} from "./tvDashboardApi";

function ok(data: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify({ success: true, data }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

describe("tvDashboardApi — histórico", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lista histórico paginado", async () => {
    const fetchMock = vi.fn(() =>
      ok({
        items: [],
        page: 2,
        pageSize: 10,
        total: 15,
        totalPages: 2,
        currentRevision: 8,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listPlaylistHistory("pl 1", { page: 2, pageSize: 10 });

    expect(fetchMock).toHaveBeenCalledWith(
      "/apps/tv-dashboard-api/playlists/pl 1/history?page=2&pageSize=10",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("carrega detalhe e restaura atomicamente com expectedRevision", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() =>
        ok({
          snapshotId: "snap/4",
          revision: 4,
          createdAt: "2026-07-16T12:00:00Z",
          playlist: { id: "pl-1", name: "Programação", slides: [] },
        }),
      )
      .mockImplementationOnce(() =>
        ok({ playlist: { id: "pl-1", revision: 9, slides: [] } }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const detail = await getPlaylistHistorySnapshot("pl-1", "snap/4");
    const restored = await restorePlaylistHistorySnapshot("pl-1", "snap/4", 8);

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/apps/tv-dashboard-api/playlists/pl-1/history/snap%2F4",
    );
    expect(fetchMock.mock.calls[1]?.[0]).toBe(
      "/apps/tv-dashboard-api/playlists/pl-1/history/snap%2F4/restore",
    );
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({ method: "POST", body: JSON.stringify({ expectedRevision: 8 }) }),
    );
    expect(detail.snapshot.slides).toEqual([]);
    expect(restored.revision).toBe(9);
  });
});
