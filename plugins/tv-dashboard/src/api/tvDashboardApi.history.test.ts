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
        items: [{
          snapshotId: "snap-8",
          revision: 8,
          createdAt: "2026-07-16T12:00:00Z",
          authorName: "Ana Souza",
          authorEmail: "ana@delpi.com.br",
          change: {
            available: true,
            comparedToRevision: 7,
            playlistFields: ["name"],
            slides: { added: ["slide-1"], removed: [], updated: [], reordered: false },
            totals: { playlistFields: 1, added: 1, removed: 0, updated: 0, reordered: 0 },
          },
        }],
        page: 2,
        pageSize: 10,
        total: 15,
        totalPages: 2,
        currentRevision: 8,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const page = await listPlaylistHistory("pl 1", { page: 2, pageSize: 10 });

    expect(fetchMock).toHaveBeenCalledWith(
      "/apps/tv-dashboard-api/playlists/pl 1/history?page=2&pageSize=10",
      expect.objectContaining({ method: "GET" }),
    );
    expect(page.items[0]).toEqual(
      expect.objectContaining({
        authorName: "Ana Souza",
        authorEmail: "ana@delpi.com.br",
        change: expect.objectContaining({ available: true, comparedToRevision: 7 }),
      }),
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
          authorName: "Ana Souza",
          authorEmail: "ana@delpi.com.br",
          change: {
            available: true,
            comparedToRevision: 3,
            playlistFields: [],
            slides: { added: [], removed: [], updated: [], reordered: true },
            totals: { reordered: 1 },
          },
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
    expect(detail.authorEmail).toBe("ana@delpi.com.br");
    expect(detail.change?.totals?.reordered).toBe(1);
    expect(restored.revision).toBe(9);
  });
});
