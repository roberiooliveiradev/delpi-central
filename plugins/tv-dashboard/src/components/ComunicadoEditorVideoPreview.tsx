import { Pause, Play, Square, Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import type { ComunicadoMediaBlock } from "@delpi/tv-dashboard-presentation";
import { ComunicadoMediaPlaceholder } from "@delpi/tv-dashboard-presentation";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";
import { resolveBrowserDisplayMediaUrl } from "../api/browserSafeMediaUrl";
import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { resolveEditorMediaUrl } from "./slideCardPreview";

type VideoBlock = ComunicadoMediaBlock;

const activeEditorVideos = new Set<HTMLVideoElement>();

function pauseOtherEditorVideos(except: HTMLVideoElement) {
  for (const video of activeEditorVideos) {
    if (video !== except && !video.paused) video.pause();
  }
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

type Props = {
  block: VideoBlock;
  style: CSSProperties;
  className?: string;
};

/**
 * Player do editor: stream via URL pública (capability) quando há publicToken;
 * senão admin+access_token; se falhar, blob autenticado.
 */
export function ComunicadoEditorVideoPreview({ block, style, className = "" }: Props) {
  const { playlistId, publicToken } = useComunicadoEditor();
  const mediaUrl = resolveEditorMediaUrl(playlistId, block.assetId, block.url);
  const streamSrc =
    playlistId && block.assetId
      ? resolveBrowserDisplayMediaUrl(playlistId, block.assetId, publicToken)
      : undefined;
  const [preferBlob, setPreferBlob] = useState(false);
  const blob = useAuthenticatedBlobUrl(preferBlob ? mediaUrl : undefined);
  const src = preferBlob ? blob.src : streamSrc;
  const loading = preferBlob ? blob.loading || (!blob.src && !blob.error) : !streamSrc;
  const hardError = preferBlob ? blob.error : false;

  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    setPreferBlob(false);
    setLoadError(false);
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  }, [mediaUrl]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;
    activeEditorVideos.add(video);
    return () => {
      activeEditorVideos.delete(video);
    };
  }, [src]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const syncTime = () => setCurrentTime(video.currentTime);
    const syncDuration = () => setDuration(Number.isFinite(video.duration) ? video.duration : 0);
    const onPlay = () => {
      pauseOtherEditorVideos(video);
      setPlaying(true);
    };
    const onPause = () => setPlaying(false);
    const onEnded = () => setPlaying(false);
    const onError = () => {
      if (!preferBlob && mediaUrl) {
        setPreferBlob(true);
        return;
      }
      setLoadError(true);
    };

    video.addEventListener("timeupdate", syncTime);
    video.addEventListener("loadedmetadata", syncDuration);
    video.addEventListener("durationchange", syncDuration);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("ended", onEnded);
    video.addEventListener("error", onError);

    return () => {
      video.removeEventListener("timeupdate", syncTime);
      video.removeEventListener("loadedmetadata", syncDuration);
      video.removeEventListener("durationchange", syncDuration);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("ended", onEnded);
      video.removeEventListener("error", onError);
    };
  }, [src, preferBlob, mediaUrl]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = muted;
    video.volume = volume;
  }, [muted, volume]);

  function handlePlay() {
    const video = videoRef.current;
    if (!video) return;
    video.muted = false;
    setMuted(false);
    pauseOtherEditorVideos(video);
    void video.play().catch(() => {
      setLoadError(true);
    });
  }

  function handlePause() {
    videoRef.current?.pause();
  }

  function handleStop() {
    const video = videoRef.current;
    if (!video) return;
    video.pause();
    video.currentTime = 0;
    setCurrentTime(0);
    setPlaying(false);
  }

  function handleSeek(next: number) {
    const video = videoRef.current;
    if (!video || !Number.isFinite(next)) return;
    video.currentTime = next;
    setCurrentTime(next);
  }

  const blockClass = ensureComunicadoDualClass(
    [
      "tdp-comunicado__block",
      "tdp-comunicado__block--video",
      "tdp-comunicado__block--media",
      "td-composer__media-block",
      "td-composer__media-block--video",
      className,
    ]
      .filter(Boolean)
      .join(" "),
  );

  let body: ReactNode;
  if (!mediaUrl) {
    body = <ComunicadoMediaPlaceholder kind="video" />;
  } else if (hardError || loadError) {
    body = <ComunicadoMediaPlaceholder kind="video" state="error" />;
  } else if (loading || !src) {
    body = <ComunicadoMediaPlaceholder kind="video" state="loading" />;
  } else {
    body = (
      <>
        <video
          key={src}
          ref={videoRef}
          className="td-composer__media-preview"
          src={src}
          playsInline
          preload="metadata"
          style={{ objectFit: block.style?.objectFit ?? "contain" }}
        />
        <div
          className="td-composer__video-controls"
          onPointerDown={(event) => event.stopPropagation()}
        >
          <button
            type="button"
            className="td-composer__video-btn"
            onClick={handlePlay}
            disabled={playing}
            title="Reproduzir com áudio"
            aria-label="Reproduzir com áudio"
          >
            <Play size={14} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="td-composer__video-btn"
            onClick={handlePause}
            disabled={!playing}
            title="Pausar"
            aria-label="Pausar"
          >
            <Pause size={14} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="td-composer__video-btn"
            onClick={handleStop}
            title="Parar"
            aria-label="Parar"
          >
            <Square size={14} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="td-composer__video-btn"
            onClick={() => setMuted((value) => !value)}
            title={muted ? "Ativar som" : "Silenciar"}
            aria-label={muted ? "Ativar som" : "Silenciar"}
          >
            {muted || volume === 0 ? (
              <VolumeX size={14} aria-hidden="true" />
            ) : (
              <Volume2 size={14} aria-hidden="true" />
            )}
          </button>
          <input
            type="range"
            className="td-composer__video-volume"
            min={0}
            max={1}
            step={0.05}
            value={muted ? 0 : volume}
            aria-label="Volume"
            onChange={(event) => {
              const next = Number(event.target.value);
              setVolume(next);
              setMuted(next === 0);
            }}
          />
          <input
            type="range"
            className="td-composer__video-seek"
            min={0}
            max={duration > 0 ? duration : 0}
            step={0.1}
            value={Math.min(currentTime, duration || 0)}
            aria-label="Posição do vídeo"
            disabled={!(duration > 0)}
            onChange={(event) => handleSeek(Number(event.target.value))}
          />
          <span className="td-composer__video-time" aria-live="polite">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </>
    );
  }

  return (
    <div className={blockClass} style={style}>
      {body}
    </div>
  );
}
