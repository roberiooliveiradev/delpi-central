import { describe, expect, it, vi } from "vitest";

import { centerSignaturePngBlob } from "./centerSignaturePngBlob";

describe("centerSignaturePngBlob", () => {
  it("devolve o original se createImageBitmap falhar", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => {
        throw new Error("unsupported");
      }),
    );
    const original = new Blob(["x"], { type: "image/png" });
    const result = await centerSignaturePngBlob(original);
    expect(result).toBe(original);
    vi.unstubAllGlobals();
  });

  it("exporta PNG centralizado quando há tinta no bitmap", async () => {
    const width = 40;
    const height = 20;
    const data = new Uint8ClampedArray(width * height * 4);
    // tinta no canto superior esquerdo
    for (let y = 0; y < 4; y += 1) {
      for (let x = 0; x < 6; x += 1) {
        const i = (y * width + x) * 4;
        data[i] = 15;
        data[i + 1] = 23;
        data[i + 2] = 42;
        data[i + 3] = 255;
      }
    }

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
      clearRect: vi.fn(),
      getImageData: vi.fn(() => ({ data, width, height })),
    };
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
      context as unknown as CanvasRenderingContext2D,
    );
    vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function toBlob(
      this: HTMLCanvasElement,
      cb: BlobCallback,
    ) {
      cb(new Blob(["centered"], { type: "image/png" }));
    });

    const original = new Blob(["src"], { type: "image/png" });
    const result = await centerSignaturePngBlob(original, {
      targetWidth: 100,
      targetHeight: 50,
      padding: 4,
    });
    expect(result).toBeInstanceOf(Blob);
    expect(context.drawImage).toHaveBeenCalled();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });
});
