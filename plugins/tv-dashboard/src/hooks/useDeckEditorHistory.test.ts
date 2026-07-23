import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  getPlaylist,
  listPlaylistHistory,
  restorePlaylistHistorySnapshot,
  type Playlist,
  type PlaylistHistoryPage,
} from "../api/tvDashboardApi";
import { HttpRequestError } from "../api/httpClient";
import { useDeckEditorHistory } from "./useDeckEditorHistory";

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/tvDashboardApi")>();
  return {
    ...actual,
    getPlaylist: vi.fn(),
    listPlaylistHistory: vi.fn(),
    restorePlaylistHistorySnapshot: vi.fn(),
  };
});

const playlist: Playlist = {
  id: "pl-1",
  publicToken: "token",
  name: "Programação",
  viewportProfile: "1080p",
  transitionStyle: "fade",
  defaultDurationSec: 30,
  globalRefreshSec: 30,
  isActive: true,
  viewCount: 0,
  slides: [],
};

function page(snapshotId: string, revision: number): PlaylistHistoryPage {
  return {
    items: [
      {
        snapshotId,
        revision,
        createdAt: "2026-07-16T12:00:00Z",
      },
    ],
    page: 1,
    pageSize: 10,
    total: 1,
    totalPages: 1,
    hasNext: false,
    currentRevision: revision,
  };
}

describe("useDeckEditorHistory", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    vi.mocked(getPlaylist).mockResolvedValue(playlist);
    vi.mocked(listPlaylistHistory).mockResolvedValue(page("snap-2", 2));
  });

  it("confirma ponteiro somente após a mutação e usa restore atômico no undo", async () => {
    const applySnapshot = vi.fn();
    const { result } = renderHook(() =>
      useDeckEditorHistory({
        playlistId: "pl-1",
        getPlaylist: () => playlist,
        getSelectedSlideId: () => null,
        getLiveComunicadoConfig: () => null,
        getComunicadoSlideId: () => null,
        applySnapshot,
      }),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.recordBeforeChange());
    expect(result.current.canUndo).toBe(false);

    vi.mocked(listPlaylistHistory).mockResolvedValue(page("snap-3", 3));
    await act(async () => result.current.confirmChange());
    expect(result.current.canUndo).toBe(true);

    vi.mocked(restorePlaylistHistorySnapshot).mockResolvedValue({
      ...playlist,
      revision: 4,
    });
    await act(async () => result.current.undo());

    expect(restorePlaylistHistorySnapshot).toHaveBeenCalledWith("pl-1", "snap-3", 3);
    expect(applySnapshot).toHaveBeenCalledWith({
      playlist: expect.objectContaining({ id: "pl-1", revision: 4 }),
      selectedSlideId: null,
    });
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(true);
  });

  it("em 409 recarrega a versão remota e invalida pilhas locais", async () => {
    const applySnapshot = vi.fn();
    const { result } = renderHook(() =>
      useDeckEditorHistory({
        playlistId: "pl-1",
        getPlaylist: () => playlist,
        getSelectedSlideId: () => null,
        getLiveComunicadoConfig: () => null,
        getComunicadoSlideId: () => null,
        applySnapshot,
      }),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    act(() => result.current.recordBeforeChange());
    vi.mocked(listPlaylistHistory).mockResolvedValue(page("snap-3", 3));
    await act(async () => result.current.confirmChange());

    vi.mocked(restorePlaylistHistorySnapshot).mockRejectedValue(
      new HttpRequestError("Conflito", 409),
    );
    await act(async () => result.current.undo());

    expect(getPlaylist).toHaveBeenCalledWith("pl-1");
    expect(applySnapshot).toHaveBeenCalledWith({ playlist, selectedSlideId: null });
    expect(result.current.error).toContain("atualizada por outra pessoa");
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(false);
  });

  it("preserva ponteiros de revisão no eco local e em atualização remota", async () => {
    const { result } = renderHook(() =>
      useDeckEditorHistory({
        playlistId: "pl-1",
        getPlaylist: () => playlist,
        getSelectedSlideId: () => null,
        getLiveComunicadoConfig: () => null,
        getComunicadoSlideId: () => null,
        applySnapshot: vi.fn(),
      }),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    act(() => result.current.recordBeforeChange());
    vi.mocked(listPlaylistHistory).mockResolvedValue(page("snap-3", 3));
    await act(async () => result.current.confirmChange());
    expect(result.current.canUndo).toBe(true);

    await act(async () => result.current.handleRemoteUpdate());
    expect(result.current.canUndo).toBe(true);

    vi.mocked(listPlaylistHistory).mockResolvedValue(page("snap-4", 4));
    await act(async () => result.current.handleRemoteUpdate());
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);
  });
});
