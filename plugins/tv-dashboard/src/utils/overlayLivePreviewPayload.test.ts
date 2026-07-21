import { describe, expect, it } from "vitest";

import type { PresentationPayload, Playlist } from "../api/tvDashboardApi";
import { overlayLiveCustomMessageSlidesOnPreviewPayload } from "./overlayLivePreviewPayload";

describe("overlayLiveCustomMessageSlidesOnPreviewPayload", () => {
  it("aplica blocks do shell local sobre o payload do servidor", () => {
    const live: Playlist = {
      id: "pl-1",
      name: "T",
      slides: [
        {
          id: "s-1",
          title: "Custom",
          slideType: "native",
          nativeScreenKey: "custom_message",
          nativeConfig: {
            blocks: [
              { id: "b1", type: "heading", content: "NOVO", frame: { x: 1, y: 2, w: 3, h: 4 } },
            ],
          },
        } as never,
      ],
    } as Playlist;

    const payload = {
      playlist: { id: "pl-1" },
      slides: [
        {
          id: "s-1",
          title: "Old",
          slideType: "native",
          native: {
            screenKey: "custom_message",
            config: { blocks: [{ id: "b1", type: "heading", content: "VELHO" }] },
            data: {
              blocks: [
                {
                  id: "b1",
                  type: "heading",
                  content: "VELHO",
                  resolved: { kpi: { value: 1 } },
                },
              ],
              master: { enabled: true, logo: { url: "https://x/logo.png" } },
            },
          },
        },
      ],
    } as unknown as PresentationPayload;

    const merged = overlayLiveCustomMessageSlidesOnPreviewPayload(payload, live);
    const blocks = (merged.slides[0].native?.data as { blocks: Array<Record<string, unknown>> })
      .blocks;
    expect(blocks[0].content).toBe("NOVO");
    expect(blocks[0].resolved).toEqual({ kpi: { value: 1 } });
    expect((merged.slides[0].native?.data as { master: unknown }).master).toEqual({
      enabled: true,
      logo: { url: "https://x/logo.png" },
    });
  });
});
