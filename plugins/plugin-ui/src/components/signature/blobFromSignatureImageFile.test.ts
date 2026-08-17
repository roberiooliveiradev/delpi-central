import { afterEach, describe, expect, it, vi } from "vitest";

import {
  blobFromSignatureImageFile,
  isSignatureImageFile,
} from "./blobFromSignatureImageFile";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("isSignatureImageFile", () => {
  it("aceita PNG/JPEG por MIME", () => {
    expect(isSignatureImageFile(new File([""], "a.png", { type: "image/png" }))).toBe(true);
    expect(isSignatureImageFile(new File([""], "a.jpg", { type: "image/jpeg" }))).toBe(true);
    expect(isSignatureImageFile(new File([""], "a.jpg", { type: "image/jpg" }))).toBe(true);
  });

  it("aceita extensão quando MIME está vazio", () => {
    expect(isSignatureImageFile(new File([""], "sign.PNG", { type: "" }))).toBe(true);
    expect(isSignatureImageFile(new File([""], "sign.jpeg", { type: "" }))).toBe(true);
  });

  it("rejeita não-imagem", () => {
    expect(isSignatureImageFile(new File([""], "doc.pdf", { type: "application/pdf" }))).toBe(
      false,
    );
    expect(isSignatureImageFile(new File([""], "doc.pdf", { type: "" }))).toBe(false);
  });
});

describe("blobFromSignatureImageFile", () => {
  it("converte arquivo com MIME vazio via createImageBitmap", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => ({
        width: 80,
        height: 30,
        close: vi.fn(),
      })),
    );
    HTMLCanvasElement.prototype.toBlob = function toBlob(cb: BlobCallback) {
      cb(new Blob(["ok"], { type: "image/png" }));
    };
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      drawImage: vi.fn(),
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

    const file = new File([new Uint8Array([1, 2, 3])], "assinatura.png", { type: "" });
    const blob = await blobFromSignatureImageFile(file, 640, 220);
    expect(blob).toBeInstanceOf(Blob);
    expect(createImageBitmap).toHaveBeenCalled();
  });

  it("usa fallback Image quando createImageBitmap falha", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => {
        throw new Error("unsupported");
      }),
    );
    const revoke = vi.fn();
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL: revoke,
    });

    class MockImage {
      width = 100;
      height = 40;
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      set src(_value: string) {
        queueMicrotask(() => this.onload?.());
      }
    }
    vi.stubGlobal("Image", MockImage);

    HTMLCanvasElement.prototype.toBlob = function toBlob(cb: BlobCallback) {
      cb(new Blob(["fallback"], { type: "image/png" }));
    };
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      drawImage: vi.fn(),
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

    const file = new File([new Uint8Array([9])], "sign.jpg", { type: "image/jpeg" });
    const blob = await blobFromSignatureImageFile(file);
    expect(blob).toBeInstanceOf(Blob);
    expect(revoke).toHaveBeenCalled();
  });

  it("retorna null para tipo inválido", async () => {
    const blob = await blobFromSignatureImageFile(
      new File([""], "x.txt", { type: "text/plain" }),
    );
    expect(blob).toBeNull();
  });
});
