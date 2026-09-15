import { useEffect, useState, type RefObject } from "react";

import {
  deriveVideoElementLoadPhase,
  type VideoElementLoadPhase,
} from "./videoElementLoadState";

export type UseVideoElementLoadStateResult = {
  phase: VideoElementLoadPhase;
  showLoadingOverlay: boolean;
};

/**
 * Observa readyState / waiting / error de um `<video>` e expõe overlay de carga.
 * Mantém o elemento montado (não substitui por placeholder) para o stream avançar.
 */
export function useVideoElementLoadState(
  videoRef: RefObject<HTMLVideoElement | null>,
  src: string | undefined,
): UseVideoElementLoadStateResult {
  const hasSrc = Boolean(src?.trim());
  const [readyState, setReadyState] = useState(0);
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setReadyState(0);
    setWaiting(false);
    setError(false);
  }, [src]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !hasSrc) return;

    const syncReady = () => {
      setReadyState(video.readyState);
      if (video.readyState >= 1) setWaiting(false);
    };
    const onWaiting = () => setWaiting(true);
    const onPlaying = () => setWaiting(false);
    const onCanPlay = () => {
      setWaiting(false);
      syncReady();
    };
    const onError = () => setError(true);

    syncReady();
    video.addEventListener("loadstart", syncReady);
    video.addEventListener("loadedmetadata", syncReady);
    video.addEventListener("loadeddata", syncReady);
    video.addEventListener("canplay", onCanPlay);
    video.addEventListener("canplaythrough", onCanPlay);
    video.addEventListener("waiting", onWaiting);
    video.addEventListener("playing", onPlaying);
    video.addEventListener("error", onError);

    return () => {
      video.removeEventListener("loadstart", syncReady);
      video.removeEventListener("loadedmetadata", syncReady);
      video.removeEventListener("loadeddata", syncReady);
      video.removeEventListener("canplay", onCanPlay);
      video.removeEventListener("canplaythrough", onCanPlay);
      video.removeEventListener("waiting", onWaiting);
      video.removeEventListener("playing", onPlaying);
      video.removeEventListener("error", onError);
    };
  }, [videoRef, src, hasSrc]);

  return deriveVideoElementLoadPhase({
    hasSrc,
    readyState,
    error,
    waiting,
  });
}
