import { describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { snapshotConfig } from "../hooks/comunicadoEditor/useComunicadoEditorHistory";
import { startLiveBlockPatchGesture } from "./comunicadoLiveBlockGesture";

function emptyConfig(): ComunicadoConfig {
  return { blocks: [] };
}

describe("startLiveBlockPatchGesture", () => {
  it("não finaliza histórico se não houve apply", () => {
    const finalizeHistoryGesture = vi.fn();
    const gesture = startLiveBlockPatchGesture(
      {
        snapshotEditorConfig: emptyConfig,
        updateBlockLive: vi.fn(),
        finalizeHistoryGesture,
      },
      "b1",
    );
    gesture.finish();
    expect(finalizeHistoryGesture).not.toHaveBeenCalled();
  });

  it("empilha um único undo após applies live", () => {
    const before = emptyConfig();
    const updateBlockLive = vi.fn();
    const finalizeHistoryGesture = vi.fn();
    const gesture = startLiveBlockPatchGesture(
      {
        snapshotEditorConfig: () => before,
        updateBlockLive,
        finalizeHistoryGesture,
      },
      "b1",
    );
    gesture.apply({ content: "a" } as never);
    gesture.apply({ content: "b" } as never);
    gesture.finish();
    expect(updateBlockLive).toHaveBeenCalledTimes(2);
    expect(finalizeHistoryGesture).toHaveBeenCalledOnce();
    expect(finalizeHistoryGesture.mock.calls[0][0]).toEqual(snapshotConfig(before));
  });
});
