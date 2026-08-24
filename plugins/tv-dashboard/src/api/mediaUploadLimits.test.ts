import { describe, expect, it } from "vitest";

import {
  MAX_VIDEO_UPLOAD_BYTES,
  detectMediaUploadKind,
  validateMediaUploadFile,
} from "./mediaUploadLimits";

describe("mediaUploadLimits", () => {
  it("detecta SVG por MIME e extensão", () => {
    expect(detectMediaUploadKind(new File([], "logo.svg", { type: "image/svg+xml" }))).toBe("image");
    expect(validateMediaUploadFile(new File([new Uint8Array(4)], "icon.svg", { type: "" }), ["image"])).toBeNull();
  });

  it("detecta imagem e vídeo por MIME e extensão", () => {
    expect(detectMediaUploadKind(new File([], "a.png", { type: "image/png" }))).toBe("image");
    expect(detectMediaUploadKind(new File([], "a.mp4", { type: "video/mp4" }))).toBe("video");
    expect(detectMediaUploadKind(new File([], "a.pdf", { type: "application/pdf" }))).toBe(null);
  });

  it("rejeita vídeo acima de 200 MB", () => {
    const big = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    Object.defineProperty(big, "size", { value: MAX_VIDEO_UPLOAD_BYTES + 1 });
    expect(validateMediaUploadFile(big, ["video"])).toMatch(/limite de 200 MB/);
  });

  it("aceita vídeo dentro do limite", () => {
    const ok = new File([new Uint8Array(8)], "clip.mp4", { type: "video/mp4" });
    expect(validateMediaUploadFile(ok, ["video"])).toBeNull();
  });
});
