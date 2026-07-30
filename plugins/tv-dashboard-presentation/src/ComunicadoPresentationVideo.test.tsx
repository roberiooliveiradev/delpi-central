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

  it("não autoplaya fora do deck de apresentação (miniatura/editor)", async () => {
    const { play } = mockMediaPlayback();

    const { queryByLabelText, container } = render(
      <PresentationPlaybackProvider deckPaused={false}>
        <div className="td-slide-thumb__stage">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(container.querySelector("video")).toBeTruthy());
    expect(play).not.toHaveBeenCalled();
    expect(queryByLabelText("Reproduzir vídeo")).toBeNull();
    expect(queryByLabelText("Pausar vídeo")).toBeNull();
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

  it("cancela autoplay pendente quando o deck pausa", async () => {
    let resolvePlay: ((value?: void) => void) | null = null;
    const play = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolvePlay = resolve;
        }),
    );
    const pause = vi.fn(function pause(this: HTMLMediaElement) {
      Object.defineProperty(this, "paused", { configurable: true, get: () => true });
      this.dispatchEvent(new Event("pause"));
    });
    vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(play);
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(pause);

    const { rerender, container } = render(
      <PresentationPlaybackProvider deckPaused={false}>
        <div className="tdp-slide tdp-slide--active">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(play).toHaveBeenCalled());
    const pauseCallsBefore = pause.mock.calls.length;

    rerender(
      <PresentationPlaybackProvider deckPaused>
        <div className="tdp-slide tdp-slide--active">
          <ComunicadoPresentationVideo src="/media/clip.mp4" />
        </div>
      </PresentationPlaybackProvider>,
    );

    await waitFor(() => expect(pause.mock.calls.length).toBeGreaterThan(pauseCallsBefore));
    resolvePlay?.();
    await Promise.resolve();
    const video = container.querySelector("video");
    expect(video?.paused).toBe(true);
  });
});
