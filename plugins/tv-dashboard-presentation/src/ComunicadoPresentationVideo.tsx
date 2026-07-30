import { Pause, Play, Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

import { usePresentationPlayback } from "./presentationPlaybackContext";

type Props = {
  src: string;
  objectFit?: CSSProperties["objectFit"];
  className?: string;
};

function isSlideActive(node: HTMLElement | null): boolean {
  if (!node) return false;
  const slide = node.closest(".tdp-slide");
  // Miniaturas / palco do editor não montam `.tdp-slide` — sem autoplay nem áudio.
  if (!slide) return false;
  if (slide.getAttribute("aria-hidden") === "true") return false;
  return slide.classList.contains("tdp-slide--active");
}

/**
 * Vídeo na apresentação/prévia: autoplay com áudio ao entrar no slide,
 * controles próprios (play/pause/mute) e sincroniza pausa com o deck.
 */
export function ComunicadoPresentationVideo({ src, objectFit = "contain", className = "" }: Props) {
  const { deckPaused } = usePresentationPlayback();
  const rootRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [slideActive, setSlideActive] = useState(false);
  const [inPresentationDeck, setInPresentationDeck] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [controlsVisible, setControlsVisible] = useState(true);
  const hideTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const slide = root.closest(".tdp-slide");
    setInPresentationDeck(Boolean(slide));
    const sync = () => setSlideActive(isSlideActive(root));
    sync();
    const observeTarget = slide ?? root;
    const observer = new MutationObserver(sync);
    observer.observe(observeTarget, { attributes: true, attributeFilter: ["class", "aria-hidden"] });
    return () => observer.disconnect();
  }, [src]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    return () => {
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
    };
  }, [src]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    let cancelled = false;

    if (!slideActive) {
      video.pause();
      video.currentTime = 0;
      return () => {
        cancelled = true;
      };
    }

    if (deckPaused) {
      video.pause();
      return () => {
        cancelled = true;
      };
    }

    video.muted = false;
    setMuted(false);

    const tryPlay = (withMuteFallback: boolean) => {
      void video.play().then(() => {
        if (cancelled) {
          video.pause();
        }
      }).catch(() => {
        if (cancelled || !withMuteFallback) return;
        video.muted = true;
        setMuted(true);
        void video.play().then(() => {
          if (cancelled) video.pause();
        }).catch(() => {
          /* Usuário usa o botão Play. */
        });
      });
    };

    tryPlay(true);

    return () => {
      cancelled = true;
      video.pause();
    };
  }, [slideActive, deckPaused, src]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = muted;
  }, [muted]);

  function bumpControls() {
    setControlsVisible(true);
    if (hideTimerRef.current != null) window.clearTimeout(hideTimerRef.current);
    hideTimerRef.current = window.setTimeout(() => {
      if (!videoRef.current?.paused) setControlsVisible(false);
    }, 2800);
  }

  useEffect(() => {
    return () => {
      if (hideTimerRef.current != null) window.clearTimeout(hideTimerRef.current);
    };
  }, []);

  function handlePlayPause() {
    const video = videoRef.current;
    if (!video) return;
    bumpControls();
    if (playing || !video.paused) {
      video.pause();
      return;
    }
    video.muted = muted;
    void video.play().catch(() => undefined);
  }

  function handleMuteToggle() {
    const video = videoRef.current;
    if (!video) return;
    bumpControls();
    const next = !muted;
    setMuted(next);
    video.muted = next;
    if (!next && video.paused && slideActive && !deckPaused) {
      void video.play().catch(() => undefined);
    }
  }

  const rootClass = ensureComunicadoDualClass(
    ["tdp-presentation-video", className].filter(Boolean).join(" "),
  );

  return (
    <div
      ref={rootRef}
      className={rootClass}
      onPointerMove={bumpControls}
      onPointerDown={bumpControls}
    >
      <video
        ref={videoRef}
        className={ensureComunicadoDualClass("tdp-presentation-video__media")}
        src={src}
        playsInline
        loop
        preload="auto"
        style={{ objectFit }}
      />
      {inPresentationDeck ? (
        <div
          className={ensureComunicadoDualClass(
            [
              "tdp-presentation-video__controls",
              controlsVisible || !playing
                ? "tdp-presentation-video__controls--visible"
                : "tdp-presentation-video__controls--hidden",
            ].join(" "),
          )}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            className={ensureComunicadoDualClass("tdp-presentation-video__btn")}
            onClick={handlePlayPause}
            title={playing ? "Pausar vídeo" : "Reproduzir vídeo"}
            aria-label={playing ? "Pausar vídeo" : "Reproduzir vídeo"}
          >
            {playing ? <Pause size={16} aria-hidden /> : <Play size={16} aria-hidden />}
          </button>
          <button
            type="button"
            className={ensureComunicadoDualClass("tdp-presentation-video__btn")}
            onClick={handleMuteToggle}
            title={muted ? "Ativar áudio" : "Silenciar"}
            aria-label={muted ? "Ativar áudio" : "Silenciar"}
          >
            {muted ? <VolumeX size={16} aria-hidden /> : <Volume2 size={16} aria-hidden />}
          </button>
          {muted ? (
            <span className={ensureComunicadoDualClass("tdp-presentation-video__hint")}>
              Toque no alto-falante para ouvir
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
