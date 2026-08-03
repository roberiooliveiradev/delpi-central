import { describe, expect, it, vi } from "vitest";

import {
  buildDataPreviewBlockRequest,
  stripBlockResolvedForPreview,
} from "./dataPreviewRequest";

vi.mock("../api/tvDashboardApi", () => ({
  previewDataBlockV2: vi.fn(),
}));

describe("dataPreviewRequest", () => {
  it("stripBlockResolvedForPreview remove resolved", () => {
    expect(
      stripBlockResolvedForPreview({
        id: "src-1",
        type: "data_source",
        resolved: { kpi: { value: 1 } },
      }),
    ).toEqual({ id: "src-1", type: "data_source" });
  });

  it("buildDataPreviewBlockRequest inclui playlistDefaults live e forceRefresh", () => {
    const body = buildDataPreviewBlockRequest({
      block: { id: "a" },
      nativeConfig: { version: 4 },
      playlistId: "pl-1",
      playlistDefaults: { branch: "02" },
      forceRefresh: true,
    });
    expect(body).toMatchObject({
      block: { id: "a" },
      nativeConfig: { version: 4 },
      playlistId: "pl-1",
      playlistDefaults: { branch: "02" },
      forceRefresh: true,
    });
  });

  it("buildDataPreviewBlockRequest omite playlistDefaults vazio/nulo", () => {
    expect(
      buildDataPreviewBlockRequest({
        block: { id: "a" },
        nativeConfig: {},
        playlistDefaults: null,
      }).playlistDefaults,
    ).toBeUndefined();
  });
});
