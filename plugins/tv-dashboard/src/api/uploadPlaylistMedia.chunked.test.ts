import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("./httpClient", async () => {
  const actual = await vi.importActual<typeof import("./httpClient")>("./httpClient");
  return {
    ...actual,
    httpPost: vi.fn(),
    httpPostForm: vi.fn(),
    httpPutBytes: vi.fn(),
    httpDelete: vi.fn(),
  };
});

import { httpDelete, httpPost, httpPostForm, httpPutBytes } from "./httpClient";
import { EDGE_SAFE_UPLOAD_CHUNK_BYTES } from "./mediaUploadLimits";
import { uploadPlaylistMedia } from "./tvDashboardApi";

describe("uploadPlaylistMedia", () => {
  beforeEach(() => {
    vi.mocked(httpPost).mockReset();
    vi.mocked(httpPostForm).mockReset();
    vi.mocked(httpPutBytes).mockReset();
    vi.mocked(httpDelete).mockReset();
  });

  it("usa POST único abaixo do limiar da borda", async () => {
    const file = new File([new Uint8Array(8)], "small.mp4", { type: "video/mp4" });
    Object.defineProperty(file, "size", { value: EDGE_SAFE_UPLOAD_CHUNK_BYTES });
    vi.mocked(httpPostForm).mockResolvedValue({
      success: true,
      data: { id: "a1", mediaKind: "video" },
    });
    const asset = await uploadPlaylistMedia("pl-1", file);
    expect(asset.id).toBe("a1");
    expect(httpPostForm).toHaveBeenCalledOnce();
    expect(httpPost).not.toHaveBeenCalled();
  });

  it("usa sessão em chunks acima do limiar da borda", async () => {
    const size = EDGE_SAFE_UPLOAD_CHUNK_BYTES + 10;
    const file = new File([new Uint8Array(8)], "big.mp4", { type: "video/mp4" });
    Object.defineProperty(file, "size", { value: size });
    vi.mocked(httpPost)
      .mockResolvedValueOnce({
        success: true,
        data: {
          uploadId: "up-1",
          chunkSizeBytes: EDGE_SAFE_UPLOAD_CHUNK_BYTES,
          chunkCount: 2,
          sizeBytes: size,
        },
      })
      .mockResolvedValueOnce({
        success: true,
        data: { id: "a2", mediaKind: "video" },
      });
    vi.mocked(httpPutBytes).mockResolvedValue({ success: true, data: { chunkIndex: 0 } });

    const asset = await uploadPlaylistMedia("pl-1", file);
    expect(asset.id).toBe("a2");
    expect(httpPostForm).not.toHaveBeenCalled();
    expect(httpPutBytes).toHaveBeenCalledTimes(2);
    expect(httpPost).toHaveBeenCalledTimes(2);
  });
});
