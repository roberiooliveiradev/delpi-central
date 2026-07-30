import { describe, expect, it } from "vitest";

import {
  collectCanvasMediaFiles,
  isEditableDropTarget,
  planCanvasMediaDrop,
} from "./canvasFileDrop";
import { MAX_VIDEO_UPLOAD_BYTES } from "../api/mediaUploadLimits";

function mockDataTransfer(files: File[]): DataTransfer {
  return {
    files: files as unknown as FileList,
    items: [] as unknown as DataTransferItemList,
    types: ["Files"],
  } as DataTransfer;
}

describe("canvasFileDrop", () => {
  it("coleta só imagem e vídeo", () => {
    const files = collectCanvasMediaFiles(
      mockDataTransfer([
        new File([], "a.png", { type: "image/png" }),
        new File([], "b.mp4", { type: "video/mp4" }),
        new File([], "c.pdf", { type: "application/pdf" }),
      ]),
    );
    expect(files.map((file) => file.name)).toEqual(["a.png", "b.mp4"]);
  });

  it("plan rejeita vídeo acima do limite", () => {
    const big = new File([new Uint8Array(4)], "big.mp4", { type: "video/mp4" });
    Object.defineProperty(big, "size", { value: MAX_VIDEO_UPLOAD_BYTES + 1 });
    const plan = planCanvasMediaDrop([big, new File([new Uint8Array(4)], "ok.png", { type: "image/png" })]);
    expect(plan.accepted.map((file) => file.name)).toEqual(["ok.png"]);
    expect(plan.errors[0]).toMatch(/big\.mp4/);
  });

  it("detecta alvo editável", () => {
    const input = document.createElement("input");
    document.body.appendChild(input);
    expect(isEditableDropTarget(input)).toBe(true);
    expect(isEditableDropTarget(document.body)).toBe(false);
    input.remove();
  });
});
