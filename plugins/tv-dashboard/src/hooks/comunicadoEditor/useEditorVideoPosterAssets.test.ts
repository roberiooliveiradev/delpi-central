import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MediaAsset } from "../../api/tvDashboardApi";

vi.mock("../../api/tvDashboardApi", () => ({
  listPlaylistMedia: vi.fn(),
}));

import { listPlaylistMedia } from "../../api/tvDashboardApi";
import { useEditorVideoPosterAssets } from "./useEditorVideoPosterAssets";

const mockedList = vi.mocked(listPlaylistMedia);

function video(id: string, hasPoster: boolean): MediaAsset {
  return {
    id,
    playlistId: "p1",
    storedName: `${id}.mp4`,
    mimeType: "video/mp4",
    mediaKind: "video",
    fileSizeBytes: 1,
    hasPoster,
  };
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("useEditorVideoPosterAssets", () => {
  it("carrega vídeos uma vez e só marca assets com hasPoster", async () => {
    mockedList.mockResolvedValue([video("teo", true), video("legacy", false)]);
    const { result } = renderHook(() => useEditorVideoPosterAssets("p1"));
    expect(result.current.posterAssets).toBeNull();
    await waitFor(() => expect(result.current.posterAssets).not.toBeNull());
    expect(mockedList).toHaveBeenCalledTimes(1);
    expect(mockedList).toHaveBeenCalledWith("p1", "video");
    expect([...(result.current.posterAssets ?? [])]).toEqual(["teo"]);
    expect(result.current.posterAssetsRef.current).toBe(result.current.posterAssets);
  });

  it("falha ao listar mantém metadado desconhecido (sem síntese de poster)", async () => {
    mockedList.mockRejectedValue(new Error("offline"));
    const { result } = renderHook(() => useEditorVideoPosterAssets("p1"));
    await waitFor(() => expect(mockedList).toHaveBeenCalled());
    await act(async () => {});
    expect(result.current.posterAssets).toBeNull();
  });

  it("asset aplicado no editor atualiza o metadado, inclusive antes da lista chegar", async () => {
    let resolveList: (items: MediaAsset[]) => void = () => {};
    mockedList.mockReturnValue(new Promise((resolve) => (resolveList = resolve)));
    const { result } = renderHook(() => useEditorVideoPosterAssets("p1"));

    act(() => result.current.registerMediaAsset(video("uploaded", true)));
    expect(result.current.posterAssets).toBeNull();

    await act(async () => resolveList([video("teo", true)]));
    expect([...(result.current.posterAssets ?? [])].sort()).toEqual(["teo", "uploaded"]);

    act(() => result.current.registerMediaAsset(video("teo", false)));
    expect([...(result.current.posterAssets ?? [])]).toEqual(["uploaded"]);
  });
});
