import { Pause, Play, Square } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import { useAuthenticatedBlobUrl } from "../hooks/useAuthenticatedBlobUrl";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { ComunicadoMediaPlaceholder } from "@delpi/tv-dashboard-presentation";

type VideoBlock = Extract<ComunicadoBlock, { type: "video" }>;

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

export function ComunicadoEditorVideoPreview({ block, style, className = "" }: Props) {
  const { src, loading, error } = useAuthenticatedBlobUrl(block.url);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const syncTime = () => setCurrentTime(video.currentTime);
    const syncDuration = () => setDuration(Number.isFinite(video.duration) ? video.duration : 0);
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onEnded = () => setPlaying(false);

    video.addEventListener("timeupdate", syncTime);
    video.addEventListener("loadedmetadata", syncDuration);
    video.addEventListener("durationchange", syncDuration);
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("ended", onEnded);

    return () => {
      video.removeEventListener("timeupdate", syncTime);
      video.removeEventListener("loadedmetadata", syncDuration);
      video.removeEventListener("durationchange", syncDuration);
      video.removeEventListener("play", onPlay);
      video.removeEventListener("pause", onPause);
      video.removeEventListener("ended", onEnded);
    };
  }, [src]);

  useEffect(() => {
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
  }, [src]);

  function handlePlay() {
    void videoRef.current?.play();
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

  const blockClass = [
    "tdp-comunicado__block",
    "tdp-comunicado__block--video",
    "tdp-comunicado__block--media",
    "td-composer__media-block",
    "td-composer__media-block--video",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  let body: ReactNode;
  if (!block.url) {
    body = <ComunicadoMediaPlaceholder kind="video" />;
  } else if (loading) {
    body = <ComunicadoMediaPlaceholder kind="video" state="loading" />;
  } else if (error || !src) {
    body = <ComunicadoMediaPlaceholder kind="video" state="error" />;
  } else {
    body = (
      <>
        <video
          ref={videoRef}
          className="td-composer__media-preview"
          src={src}
          playsInline
          muted
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
            title="Reproduzir"
            aria-label="Reproduzir"
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
