import { describe, expect, it } from "vitest";

import {
  comunicadoBlocksHaveVideo,
  deriveVideoElementLoadPhase,
  presentationSlidesHaveVideo,
  slideNativeHasVideo,
  VIDEO_HAVE_METADATA,
} from "./videoElementLoadState";

describe("deriveVideoElementLoadPhase", () => {
  it("positive: sem metadados → loading + overlay", () => {
    expect(
      deriveVideoElementLoadPhase({
        hasSrc: true,
        readyState: 0,
        error: false,
      }),
    ).toEqual({ phase: "loading", showLoadingOverlay: true });
  });

  it("sibling: waiting após metadados → overlay de buffer", () => {
    expect(
      deriveVideoElementLoadPhase({
        hasSrc: true,
        readyState: VIDEO_HAVE_METADATA,
        error: false,
        waiting: true,
      }),
    ).toEqual({ phase: "loading", showLoadingOverlay: true });
  });

  it("negative: readyState com metadados e sem waiting → sem overlay", () => {
    expect(
      deriveVideoElementLoadPhase({
        hasSrc: true,
        readyState: VIDEO_HAVE_METADATA,
        error: false,
        waiting: false,
      }),
    ).toEqual({ phase: "ready", showLoadingOverlay: false });
  });

  it("sem src → idle", () => {
    expect(
      deriveVideoElementLoadPhase({
        hasSrc: false,
        readyState: 0,
        error: false,
      }),
    ).toEqual({ phase: "idle", showLoadingOverlay: false });
  });

  it("error → phase error sem overlay de loading", () => {
    expect(
      deriveVideoElementLoadPhase({
        hasSrc: true,
        readyState: 0,
        error: true,
      }),
    ).toEqual({ phase: "error", showLoadingOverlay: false });
  });
});

describe("presentationSlidesHaveVideo", () => {
  it("detecta bloco video em native.data.blocks", () => {
    expect(
      presentationSlidesHaveVideo([
        { native: { data: { blocks: [{ type: "heading" }, { type: "video" }] } } },
      ]),
    ).toBe(true);
  });

  it("negative: só imagem/texto", () => {
    expect(
      presentationSlidesHaveVideo([
        { native: { data: { blocks: [{ type: "image" }, { type: "text" }] } } },
      ]),
    ).toBe(false);
  });

  it("slideNativeHasVideo / comunicadoBlocksHaveVideo", () => {
    expect(slideNativeHasVideo({ data: { blocks: [{ type: "video" }] } })).toBe(true);
    expect(comunicadoBlocksHaveVideo([{ type: "shape" }])).toBe(false);
  });
});
