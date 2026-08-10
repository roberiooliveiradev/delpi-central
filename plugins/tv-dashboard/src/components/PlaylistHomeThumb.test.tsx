import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { PlaylistHomeThumb } from "./PlaylistHomeThumb";

const slideCardThumbnail = vi.fn(() => <div data-testid="thumbnail" />);

vi.mock("./SlideCardThumbnail", () => ({
  SlideCardThumbnail: (props: unknown) => slideCardThumbnail(props),
}));

describe("PlaylistHomeThumb", () => {
  it("usa mídia admin autenticada na home, inclusive para programação inativa", () => {
    const coverSlide: Slide = {
      id: "slide-1",
      playlistId: "playlist-1",
      sortOrder: 0,
      slideType: "native",
      title: "Capa",
      nativeScreenKey: "custom_message",
      nativeConfig: {},
      isActive: true,
    };

    render(
      <PlaylistHomeThumb
        playlist={{
          id: "playlist-1",
          viewportProfile: "1080p",
          coverSlide,
          publicToken: "token-que-nao-deve-ser-usado",
        }}
      />,
    );

    const props = slideCardThumbnail.mock.calls.at(-1)?.[0] as
      | Record<string, unknown>
      | undefined;
    expect(props).toMatchObject({ playlistId: "playlist-1" });
    expect(props).not.toHaveProperty("publicToken");
  });
});
