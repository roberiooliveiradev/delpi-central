import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/tvDashboardApi", async () => {
  const actual = await vi.importActual<typeof import("../api/tvDashboardApi")>(
    "../api/tvDashboardApi",
  );
  return {
    ...actual,
    getPlaylist: vi.fn(),
    uploadSlideRenderedPreview: vi.fn(),
  };
});
vi.mock("./exportSlidePng", () => ({
  resolveSlideExportTarget: vi.fn(),
  captureSlideElementToPngDataUrl: vi.fn(),
}));

import { getPlaylist, uploadSlideRenderedPreview } from "../api/tvDashboardApi";
import {
  captureSlideElementToPngDataUrl,
  resolveSlideExportTarget,
} from "./exportSlidePng";
import { handleVisualCaptureRequest } from "./liveStageVisualCapture";

const PNG_DATA_URL =
  "data:image/png;base64," + btoa("\x89PNG\r\n\x1a\n" + "fake-bytes");

const EVENT = {
  type: "visual_capture_request" as const,
  playlistId: "p1",
  slideId: "s1",
  revision: 5,
  requestId: "req-1",
};

function ctx(over: Record<string, unknown> = {}) {
  return {
    playlistId: "p1",
    getSelectedSlideId: vi.fn(() => "s1"),
    getLocalRevision: vi.fn(() => 5),
    reloadFromServer: vi.fn(async () => undefined),
    isEditorActive: vi.fn(() => true),
    getClientId: vi.fn(() => "c-9"),
    hasPendingLocalEdits: vi.fn(() => false),
    ...over,
  };
}

describe("handleVisualCaptureRequest — VISTA live-editor capture", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getPlaylist).mockResolvedValue({ revision: 5 } as never);
    vi.mocked(resolveSlideExportTarget).mockReturnValue(
      document.createElement("div"),
    );
    vi.mocked(captureSlideElementToPngDataUrl).mockResolvedValue(PNG_DATA_URL);
    vi.mocked(uploadSlideRenderedPreview).mockResolvedValue({
      status: "ready",
    } as never);
  });

  it("captures the live stage and uploads revision-bound PNG with clientId", async () => {
    const c = ctx();
    const result = await handleVisualCaptureRequest(EVENT, c);
    expect(result).toBe("captured");
    expect(captureSlideElementToPngDataUrl).toHaveBeenCalledOnce();
    expect(uploadSlideRenderedPreview).toHaveBeenCalledWith(
      "p1",
      "s1",
      5,
      expect.any(Blob),
      { clientId: "c-9" },
    );
  });

  it("ignores request for another playlist", async () => {
    const result = await handleVisualCaptureRequest(
      { ...EVENT, playlistId: "other" },
      ctx(),
    );
    expect(result).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("never captures a slide that is not visible (wrong slide → skip, no switch)", async () => {
    const c = ctx({ getSelectedSlideId: vi.fn(() => "s-other") });
    const result = await handleVisualCaptureRequest(EVENT, c);
    expect(result).toBe("skipped");
    expect(captureSlideElementToPngDataUrl).not.toHaveBeenCalled();
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("skips when the editor page is not active", async () => {
    const c = ctx({ isEditorActive: vi.fn(() => false) });
    expect(await handleVisualCaptureRequest(EVENT, c)).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("skips without a presence clientId (no live-editor provenance)", async () => {
    const c = ctx({ getClientId: vi.fn(() => null) });
    expect(await handleVisualCaptureRequest(EVENT, c)).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("skips when the authoritative revision moved past the request (race)", async () => {
    vi.mocked(getPlaylist).mockResolvedValue({ revision: 6 } as never);
    const result = await handleVisualCaptureRequest(EVENT, ctx());
    expect(result).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("reloads authoritative state when local revision lags, then captures", async () => {
    let local = 4;
    const c = ctx({
      getLocalRevision: vi.fn(() => local),
      reloadFromServer: vi.fn(async () => {
        local = 5;
      }),
    });
    const result = await handleVisualCaptureRequest(EVENT, c);
    expect(result).toBe("captured");
    expect(c.reloadFromServer).toHaveBeenCalledOnce();
  });

  it("skips when reload cannot reach the requested revision", async () => {
    const c = ctx({ getLocalRevision: vi.fn(() => 4) });
    const result = await handleVisualCaptureRequest(EVENT, c);
    expect(result).toBe("skipped");
    expect(c.reloadFromServer).toHaveBeenCalledOnce();
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("never captures pre-ack optimistic state (pending local edits)", async () => {
    const c = ctx({ hasPendingLocalEdits: vi.fn(() => true) });
    expect(await handleVisualCaptureRequest(EVENT, c)).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("skips when the stage element is not mounted", async () => {
    vi.mocked(resolveSlideExportTarget).mockReturnValue(null);
    expect(await handleVisualCaptureRequest(EVENT, ctx())).toBe("skipped");
    expect(uploadSlideRenderedPreview).not.toHaveBeenCalled();
  });

  it("upload failure degrades silently (caller retries bounded)", async () => {
    vi.mocked(uploadSlideRenderedPreview).mockRejectedValue(new Error("409"));
    expect(await handleVisualCaptureRequest(EVENT, ctx())).toBe("skipped");
  });
});
