import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ComunicadoPresentationVideo } from "./ComunicadoPresentationVideo";
import { PresentationPlaybackProvider } from "./presentationPlaybackContext";

function mockMediaPlayback() {
  const play = vi.fn(function play(this: HTMLMediaElement) {
    Object.defineProperty(this, "paused", { configurable: true, get: () => false });
    this.dispatchEvent(new Event("play"));
    return Promise.resolve();
  });
  const pause = vi.fn(function pause(this: HTMLMediaElement) {
    Object.defineProperty(this, "paused", { configurable: true, get: () => true });
    this.dispatchEvent(new Event("pause"));
  });
  vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(play);
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(pause);
  return { play, pause };
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ComunicadoPresentationVideo", () => {
  it("tenta autoplay com áudio ao montar e expõe play/pause", async () => {
    const { play, pause } = mockMediaPlayback();

    const { getByLabelText } = render(
      <PresentationPlaybackProvider deckPaused={false}>
        <div className="tdp-slide tdp-slide--active">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(play).toHaveBeenCalled());
    await waitFor(() => expect(getByLabelText("Pausar vídeo")).toBeTruthy());

    fireEvent.click(getByLabelText("Pausar vídeo"));
    expect(pause).toHaveBeenCalled();
  });

  it("pausa o vídeo quando o deck está pausado", async () => {
    const { play, pause } = mockMediaPlayback();

    const { rerender } = render(
      <PresentationPlaybackProvider deckPaused={false}>
        <div className="tdp-slide tdp-slide--active">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(play).toHaveBeenCalled());

    rerender(
      <PresentationPlaybackProvider deckPaused>
        <div className="tdp-slide tdp-slide--active">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(pause).toHaveBeenCalled());
  });
});
