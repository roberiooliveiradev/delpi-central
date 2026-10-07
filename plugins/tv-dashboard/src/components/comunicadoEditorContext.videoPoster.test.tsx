import { act, cleanup, render, waitFor } from "@testing-library/react";
import { useEffect, useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MediaAsset } from "../api/tvDashboardApi";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { useComunicadoEditor, type ComunicadoEditorContextValue } from "./comunicadoEditorContextCore";

const listPlaylistMedia = vi.fn();

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/tvDashboardApi")>();
  return {
    ...actual,
    listPlaylistMedia: (...args: unknown[]) => listPlaylistMedia(...args),
  };
});

const TEO = "8a9c5a28-teo";
const LEGACY = "72e3abbd-legacy";
const SIBLING = "legacy-sibling";
const frame = { x: 0, y: 0, w: 30, h: 20 };

function video(id: string, hasPoster: boolean): MediaAsset {
  return {
    id,
    playlistId: "pl-1",
    storedName: `${id}.mp4`,
    mimeType: "video/mp4",
    mediaKind: "video",
    fileSizeBytes: 1,
    hasPoster,
  };
}

function slideValue(...assetIds: string[]): Record<string, unknown> {
  return {
    version: 2,
    blocks: assetIds.map((assetId, index) => ({ id: `v-${index}`, type: "video", assetId, frame })),
  };
}

let api: ComunicadoEditorContextValue | null = null;
function Probe() {
  const current = useComunicadoEditor();
  useEffect(() => {
    api = current;
  });
  return null;
}

const emitted: Record<string, unknown>[] = [];

function Harness({ slideId, initial }: { slideId: string; initial: Record<string, unknown> }) {
  const [value, setValue] = useState(initial);
  const [currentSlide, setCurrentSlide] = useState(slideId);
  if (currentSlide !== slideId) {
    setCurrentSlide(slideId);
    setValue(initial);
  }
  return (
    <ComunicadoEditorProvider
      playlistId="pl-1"
      slideId={slideId}
      value={value}
      onChange={(next) => {
        emitted.push(next);
        setValue(next);
      }}
    >
      <Probe />
    </ComunicadoEditorProvider>
  );
}

function posterOf(assetId: string): string | undefined {
  const block = api?.config.blocks?.find(
    (candidate) => candidate.type === "video" && candidate.assetId === assetId,
  );
  return block && block.type === "video" ? block.posterUrl : undefined;
}

afterEach(() => {
  cleanup();
  api = null;
  emitted.length = 0;
  listPlaylistMedia.mockReset();
});

describe("ComunicadoEditorProvider — poster de vídeo hidratado de hasPoster", () => {
  it("hidrata só hasPoster=true, sobrevive a undo e troca de slide, nunca persiste", async () => {
    listPlaylistMedia.mockResolvedValue([video(TEO, true), video(LEGACY, false), video(SIBLING, false)]);
    const view = render(<Harness slideId="s1" initial={slideValue(TEO, LEGACY)} />);

    expect(posterOf(TEO)).toBeUndefined();
    await waitFor(() => expect(posterOf(TEO)).toMatch(new RegExp(`/media/${TEO}/poster$`)));
    expect(listPlaylistMedia).toHaveBeenCalledTimes(1);
    expect(listPlaylistMedia).toHaveBeenCalledWith("pl-1", "video");
    expect(posterOf(LEGACY)).toBeUndefined();
    expect(emitted).toHaveLength(0);

    act(() => api!.setSelectedId("v-1"));
    act(() => api!.removeSelected());
    expect(api!.config.blocks).toHaveLength(1);
    act(() => api!.undo());
    expect(api!.config.blocks).toHaveLength(2);
    expect(posterOf(TEO)).toMatch(/\/poster$/);
    expect(posterOf(LEGACY)).toBeUndefined();

    view.rerender(<Harness slideId="s2" initial={slideValue(SIBLING, TEO)} />);
    expect(posterOf(TEO)).toMatch(/\/poster$/);
    expect(posterOf(SIBLING)).toBeUndefined();
    expect(listPlaylistMedia).toHaveBeenCalledTimes(1);

    expect(emitted.length).toBeGreaterThan(0);
    for (const payload of emitted) {
      expect(JSON.stringify(payload)).not.toContain("posterUrl");
      expect(JSON.stringify(payload)).not.toContain("/poster");
    }
  });

  it("falha do metadado: nenhum vídeo recebe posterUrl", async () => {
    listPlaylistMedia.mockRejectedValue(new Error("offline"));
    render(<Harness slideId="s1" initial={slideValue(TEO, LEGACY)} />);
    await waitFor(() => expect(listPlaylistMedia).toHaveBeenCalled());
    await act(async () => {});
    expect(posterOf(TEO)).toBeUndefined();
    expect(posterOf(LEGACY)).toBeUndefined();
  });
});
