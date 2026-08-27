import { describe, expect, it, vi } from "vitest";

import { normalizeSignatureDisplayPngBlob } from "./normalizeSignatureDisplayPngBlob";

describe("normalizeSignatureDisplayPngBlob", () => {
  it("devolve o original se createImageBitmap falhar", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => {
        throw new Error("unsupported");
      }),
    );
    const original = new Blob(["x"], { type: "image/png" });
    const result = await normalizeSignatureDisplayPngBlob(original);
    expect(result).toBe(original);
    vi.unstubAllGlobals();
  });

  it("remove alpha de pixels brancos preservando tinta escura", async () => {
    const width = 3;
    const height = 1;
    const data = new Uint8ClampedArray([
      255, 255, 255, 255,
      10, 20, 30, 255,
      250, 250, 250, 255,
    ]);

    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => ({
        width,
        height,
        close: vi.fn(),
      })),
    );

    const context = {
      drawImage: vi.fn(),
      getImageData: vi.fn(() => ({ data, width, height })),
      putImageData: vi.fn(),
    };
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
      context as unknown as CanvasRenderingContext2D,
    );
    vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function toBlob(
      _this: HTMLCanvasElement,
      cb: BlobCallback,
    ) {
      cb(new Blob(["normalized"], { type: "image/png" }));
    });

    const original = new Blob(["src"], { type: "image/png" });
    const result = await normalizeSignatureDisplayPngBlob(original);
    expect(result).toBeInstanceOf(Blob);
    expect(data[3]).toBe(0);
    expect(data[7]).toBe(255);
    expect(data[11]).toBe(0);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });
});
