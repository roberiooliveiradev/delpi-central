import { describe, expect, it } from "vitest";

import {
  collectNextSlideVideoPrefetchUrls,
  collectSlideVideoMediaUrls,
  nextPresentationSlideIndex,
} from "./presentationMediaPrefetch";

describe("presentationMediaPrefetch", () => {
  it("positive: coleta url e posterUrl de blocos video", () => {
    expect(
      collectSlideVideoMediaUrls({
        data: {
          blocks: [
            { type: "heading" },
            {
              type: "video",
              url: "/media/v1",
              posterUrl: "/media/v1/poster",
            },
          ],
        },
      }),
    ).toEqual([{ videoUrl: "/media/v1", posterUrl: "/media/v1/poster" }]);
  });

  it("sibling: slide sem vídeo → prefetch vazio", () => {
    expect(
      collectNextSlideVideoPrefetchUrls(
        [
          { native: { data: { blocks: [{ type: "video", url: "/a" }] } } },
          { native: { data: { blocks: [{ type: "image", url: "/i" }] } } },
        ],
        0,
      ),
    ).toEqual([]);
  });

  it("negative: wrap no último slide prefetches o primeiro com vídeo", () => {
    const slides = [
      {
        native: {
          data: {
            blocks: [{ type: "video", url: "/first", posterUrl: "/first/poster" }],
          },
        },
      },
      { native: { data: { blocks: [{ type: "text" }] } } },
    ];
    expect(nextPresentationSlideIndex(1, slides.length)).toBe(0);
    expect(collectNextSlideVideoPrefetchUrls(slides, 1)).toEqual([
      "/first/poster",
      "/first",
    ]);
  });
});
