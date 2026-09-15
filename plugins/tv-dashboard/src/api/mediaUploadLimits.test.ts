import { describe, expect, it } from "vitest";

import {
  MAX_VIDEO_UPLOAD_BYTES,
  RECOMMENDED_VIDEO_MAX_HEIGHT_PX,
  detectMediaUploadKind,
  validateMediaUploadFile,
  videoResolutionWarningMessage,
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

  it("rejeita vídeo acima de 500 MB", () => {
    const big = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    Object.defineProperty(big, "size", { value: MAX_VIDEO_UPLOAD_BYTES + 1 });
    expect(validateMediaUploadFile(big, ["video"])).toMatch(/limite de 500 MB/);
  });

  it("aceita vídeo dentro do limite", () => {
    const ok = new File([new Uint8Array(8)], "clip.mp4", { type: "video/mp4" });
    Object.defineProperty(ok, "size", { value: Math.floor(MAX_VIDEO_UPLOAD_BYTES / 2) });
    expect(validateMediaUploadFile(ok, ["video"])).toBeNull();
  });

  it("avisa resolução acima de 1080p sem bloquear", () => {
    expect(videoResolutionWarningMessage(1080)).toBeNull();
    expect(videoResolutionWarningMessage(RECOMMENDED_VIDEO_MAX_HEIGHT_PX)).toBeNull();
    expect(videoResolutionWarningMessage(2160)).toMatch(/2160p/);
    expect(videoResolutionWarningMessage(2160)).toMatch(/1080p/);
  });
});
