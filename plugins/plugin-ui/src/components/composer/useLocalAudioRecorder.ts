import { useCallback, useEffect, useRef, useState } from "react";
import {
  isLocalAudioCaptureSupported,
  pickSupportedAudioRecorderMime,
} from "./audioRecorderMime";
import type {
  AudioRecorderCaptureErrorReason,
  AudioRecorderUiStatus,
  LocalAudioDraft,
} from "./audioRecorderTypes";

export type UseLocalAudioRecorderOptions = {
  enabled: boolean;
  disabled?: boolean;
  busy?: boolean;
  maxDurationMs?: number;
  maxBytes?: number;
  onDraftReady?: (draft: LocalAudioDraft) => void;
  onDiscard?: () => void;
  onCaptureError?: (reason: AudioRecorderCaptureErrorReason) => void;
  onBlockingChange?: (blocking: boolean) => void;
};

export type UseLocalAudioRecorderResult = {
  status: AudioRecorderUiStatus;
  errorReason: AudioRecorderCaptureErrorReason | null;
  durationMs: number;
  draft: LocalAudioDraft | null;
  objectUrl: string | null;
  levels: number[];
  isPlaying: boolean;
  playbackProgress: number;
  start: () => void;
  cancel: () => void;
  stop: () => void;
  discard: () => void;
  rerecord: () => void;
  togglePlayback: () => void;
  clearError: () => void;
};

function mapGetUserMediaError(err: unknown): AudioRecorderCaptureErrorReason {
  const name =
    err && typeof err === "object" && "name" in err
      ? String((err as { name?: string }).name)
      : "";
  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    return "permission_denied";
  }
  if (name === "NotFoundError" || name === "DevicesNotFoundError") {
    return "device_not_found";
  }
  if (name === "NotReadableError" || name === "TrackStartError") {
    return "device_not_readable";
  }
  if (name === "SecurityError") {
    return "secure_context_required";
  }
  return "unknown";
}

function isBlockingStatus(status: AudioRecorderUiStatus): boolean {
  return (
    status === "requesting_permission" ||
    status === "recording" ||
    status === "stopping"
  );
}

export function useLocalAudioRecorder(
  options: UseLocalAudioRecorderOptions,
): UseLocalAudioRecorderResult {
  const {
    enabled,
    disabled = false,
    busy = false,
    maxDurationMs,
    maxBytes,
    onDraftReady,
    onDiscard,
    onCaptureError,
    onBlockingChange,
  } = options;

  const limitsApproved =
    typeof maxDurationMs === "number" &&
    maxDurationMs > 0 &&
    typeof maxBytes === "number" &&
    maxBytes > 0;

  const captureAdmitted =
    enabled && limitsApproved && isLocalAudioCaptureSupported();

  const [status, setStatus] = useState<AudioRecorderUiStatus>(() =>
    captureAdmitted ? "idle" : "unavailable",
  );
  const [errorReason, setErrorReason] =
    useState<AudioRecorderCaptureErrorReason | null>(null);
  const [durationMs, setDurationMs] = useState(0);
  const [draft, setDraft] = useState<LocalAudioDraft | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [levels, setLevels] = useState<number[]>(() => Array(24).fill(0.08));
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);

  const statusRef = useRef(status);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAtRef = useRef(0);
  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const mimeRef = useRef<string>("");
  const stopReasonRef = useRef<"user" | "limit_duration" | "limit_bytes">(
    "user",
  );
  const mountedRef = useRef(true);
  const startEpochRef = useRef(0);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    onBlockingChange?.(isBlockingStatus(status));
  }, [status, onBlockingChange]);

  const revokeObjectUrl = useCallback(() => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    setObjectUrl(null);
  }, []);

  const stopTracks = useCallback(() => {
    const stream = streamRef.current;
    streamRef.current = null;
    if (!stream) return;
    for (const track of stream.getTracks()) {
      try {
        track.stop();
      } catch {
        /* ignore */
      }
    }
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current != null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const stopRaf = useCallback(() => {
    if (rafRef.current != null) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const closeAudioGraph = useCallback(() => {
    stopRaf();
    analyserRef.current = null;
    const ctx = audioCtxRef.current;
    audioCtxRef.current = null;
    if (ctx && ctx.state !== "closed") {
      void ctx.close().catch(() => undefined);
    }
  }, [stopRaf]);

  const stopPlayback = useCallback(() => {
    const el = audioElRef.current;
    if (el) {
      el.pause();
      el.removeAttribute("src");
      el.load();
    }
    audioElRef.current = null;
    setIsPlaying(false);
    setPlaybackProgress(0);
  }, []);

  const hardCleanup = useCallback(() => {
    startEpochRef.current += 1;
    const recorder = recorderRef.current;
    recorderRef.current = null;
    if (recorder && recorder.state !== "inactive") {
      try {
        recorder.stop();
      } catch {
        /* ignore */
      }
    }
    stopTimer();
    closeAudioGraph();
    stopTracks();
    stopPlayback();
    chunksRef.current = [];
  }, [closeAudioGraph, stopPlayback, stopTimer, stopTracks]);

  const fail = useCallback(
    (reason: AudioRecorderCaptureErrorReason) => {
      hardCleanup();
      revokeObjectUrl();
      setDraft(null);
      setDurationMs(0);
      setLevels(Array(24).fill(0.08));
      setErrorReason(reason);
      setStatus("error");
      onCaptureError?.(reason);
    },
    [hardCleanup, onCaptureError, revokeObjectUrl],
  );

  const resetToIdle = useCallback(() => {
    hardCleanup();
    revokeObjectUrl();
    setDraft(null);
    setDurationMs(0);
    setLevels(Array(24).fill(0.08));
    setErrorReason(null);
    setStatus(captureAdmitted ? "idle" : "unavailable");
  }, [captureAdmitted, hardCleanup, revokeObjectUrl]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      hardCleanup();
      revokeObjectUrl();
    };
  }, [hardCleanup, revokeObjectUrl]);

  useEffect(() => {
    if (!captureAdmitted) {
      if (
        statusRef.current === "recording" ||
        statusRef.current === "requesting_permission" ||
        statusRef.current === "stopping"
      ) {
        hardCleanup();
        revokeObjectUrl();
        setDraft(null);
      }
      setStatus("unavailable");
      return;
    }
    if (statusRef.current === "unavailable") {
      setStatus("idle");
    }
  }, [captureAdmitted, hardCleanup, revokeObjectUrl]);

  const startLevelLoop = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      const node = analyserRef.current;
      if (!node) return;
      node.getByteTimeDomainData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i += 1) {
        const v = (data[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / data.length);
      const level = Math.min(1, Math.max(0.06, rms * 4));
      setLevels((prev) => {
        const next = prev.slice(1);
        next.push(level);
        return next;
      });
      rafRef.current = window.requestAnimationFrame(tick);
    };
    rafRef.current = window.requestAnimationFrame(tick);
  }, []);

  const finalizeBlob = useCallback(() => {
    const mimeType = mimeRef.current || "audio/webm";
    const blob = new Blob(chunksRef.current, { type: mimeType });
    chunksRef.current = [];
    closeAudioGraph();
    stopTracks();
    stopTimer();

    const sizeBytes = blob.size;
    const measuredDuration = Math.max(0, Date.now() - startedAtRef.current);
    // The auto-stop interval can overshoot the limit by up to one tick —
    // the recorded media cannot exceed the enforced stop, so the reported
    // duration is clamped to the admitted bound (never over the contract).
    const boundedDuration =
      typeof maxDurationMs === "number"
        ? Math.min(measuredDuration, maxDurationMs)
        : measuredDuration;

    if (typeof maxBytes === "number" && sizeBytes > maxBytes) {
      fail("limit_bytes");
      return;
    }

    const nextDraft: LocalAudioDraft = {
      blob,
      mimeType,
      durationMs: boundedDuration,
      sizeBytes,
    };

    revokeObjectUrl();
    const url = URL.createObjectURL(blob);
    objectUrlRef.current = url;
    setObjectUrl(url);
    setDraft(nextDraft);
    setDurationMs(boundedDuration);
    setStatus("preview");
    onDraftReady?.(nextDraft);

    if (stopReasonRef.current === "limit_duration") {
      setErrorReason("limit_duration");
    } else if (stopReasonRef.current === "limit_bytes") {
      setErrorReason("limit_bytes");
    }
  }, [
    closeAudioGraph,
    fail,
    maxBytes,
    maxDurationMs,
    onDraftReady,
    revokeObjectUrl,
    stopTimer,
    stopTracks,
  ]);

  const start = useCallback(() => {
    if (!captureAdmitted || disabled || busy) return;
    if (
      statusRef.current !== "idle" &&
      statusRef.current !== "error" &&
      statusRef.current !== "preview"
    ) {
      return;
    }

    const mime = pickSupportedAudioRecorderMime();
    if (mime === null) {
      fail("mime_unsupported");
      return;
    }

    startEpochRef.current += 1;
    const epoch = startEpochRef.current;
    stopPlayback();
    revokeObjectUrl();
    setDraft(null);
    setErrorReason(null);
    setDurationMs(0);
    setLevels(Array(24).fill(0.08));
    setStatus("requesting_permission");
    chunksRef.current = [];
    stopReasonRef.current = "user";
    mimeRef.current = mime;

    void (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false,
        });
        if (!mountedRef.current || epoch !== startEpochRef.current) {
          for (const track of stream.getTracks()) track.stop();
          return;
        }

        streamRef.current = stream;

        try {
          const Ctx =
            window.AudioContext ||
            (
              window as unknown as {
                webkitAudioContext?: typeof AudioContext;
              }
            ).webkitAudioContext;
          if (Ctx) {
            const ctx = new Ctx();
            const source = ctx.createMediaStreamSource(stream);
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);
            audioCtxRef.current = ctx;
            analyserRef.current = analyser;
            startLevelLoop();
          }
        } catch {
          /* waveform optional */
        }

        const recorder = new MediaRecorder(
          stream,
          mime ? { mimeType: mime } : undefined,
        );
        recorderRef.current = recorder;
        mimeRef.current = recorder.mimeType || mime || "audio/webm";

        recorder.ondataavailable = (event) => {
          if (event.data && event.data.size > 0) {
            chunksRef.current.push(event.data);
            if (
              typeof maxBytes === "number" &&
              chunksRef.current.reduce(
                (acc, part) =>
                  acc + (part instanceof Blob ? part.size : 0),
                0,
              ) > maxBytes
            ) {
              stopReasonRef.current = "limit_bytes";
              if (recorder.state === "recording") {
                try {
                  recorder.stop();
                } catch {
                  /* ignore */
                }
              }
            }
          }
        };

        recorder.onerror = () => {
          if (epoch !== startEpochRef.current) return;
          fail("recorder_failed");
        };

        recorder.onstop = () => {
          if (epoch !== startEpochRef.current) return;
          if (!mountedRef.current) return;
          finalizeBlob();
        };

        startedAtRef.current = Date.now();
        recorder.start(250);
        setStatus("recording");

        stopTimer();
        timerRef.current = window.setInterval(() => {
          const elapsed = Date.now() - startedAtRef.current;
          setDurationMs(
            typeof maxDurationMs === "number"
              ? Math.min(elapsed, maxDurationMs)
              : elapsed,
          );
          if (
            typeof maxDurationMs === "number" &&
            elapsed >= maxDurationMs
          ) {
            stopReasonRef.current = "limit_duration";
            const active = recorderRef.current;
            if (active && active.state === "recording") {
              setStatus("stopping");
              try {
                active.stop();
              } catch {
                fail("recorder_failed");
              }
            }
          }
        }, 200);
      } catch (err) {
        if (!mountedRef.current || epoch !== startEpochRef.current) return;
        fail(mapGetUserMediaError(err));
      }
    })();
  }, [
    busy,
    captureAdmitted,
    disabled,
    fail,
    finalizeBlob,
    maxBytes,
    maxDurationMs,
    revokeObjectUrl,
    startLevelLoop,
    stopPlayback,
    stopTimer,
  ]);

  const cancel = useCallback(() => {
    if (
      statusRef.current !== "recording" &&
      statusRef.current !== "requesting_permission" &&
      statusRef.current !== "stopping"
    ) {
      return;
    }
    startEpochRef.current += 1;
    hardCleanup();
    revokeObjectUrl();
    setDraft(null);
    setDurationMs(0);
    setLevels(Array(24).fill(0.08));
    setErrorReason(null);
    setStatus("idle");
    onDiscard?.();
  }, [hardCleanup, onDiscard, revokeObjectUrl]);

  const stop = useCallback(() => {
    if (statusRef.current !== "recording") return;
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    stopReasonRef.current = "user";
    setStatus("stopping");
    try {
      recorder.stop();
    } catch {
      fail("recorder_failed");
    }
  }, [fail]);

  const discard = useCallback(() => {
    hardCleanup();
    revokeObjectUrl();
    setDraft(null);
    setDurationMs(0);
    setLevels(Array(24).fill(0.08));
    setErrorReason(null);
    setStatus("idle");
    onDiscard?.();
  }, [hardCleanup, onDiscard, revokeObjectUrl]);

  const rerecord = useCallback(() => {
    hardCleanup();
    revokeObjectUrl();
    setDraft(null);
    setDurationMs(0);
    setLevels(Array(24).fill(0.08));
    setErrorReason(null);
    setStatus("idle");
    // start on next tick so status settles to idle first
    window.setTimeout(() => {
      if (!mountedRef.current) return;
      start();
    }, 0);
  }, [hardCleanup, revokeObjectUrl, start]);

  const togglePlayback = useCallback(() => {
    if (!objectUrlRef.current || statusRef.current !== "preview") return;
    let el = audioElRef.current;
    if (!el) {
      el = new Audio(objectUrlRef.current);
      audioElRef.current = el;
      el.onended = () => {
        setIsPlaying(false);
        setPlaybackProgress(1);
      };
      el.ontimeupdate = () => {
        if (!el || !el.duration || !Number.isFinite(el.duration)) return;
        setPlaybackProgress(el.currentTime / el.duration);
      };
    }
    if (el.paused) {
      void el.play().then(
        () => setIsPlaying(true),
        () => setIsPlaying(false),
      );
    } else {
      el.pause();
      setIsPlaying(false);
    }
  }, []);

  const clearError = useCallback(() => {
    if (statusRef.current !== "error") return;
    resetToIdle();
  }, [resetToIdle]);

  return {
    status: captureAdmitted
      ? status === "unavailable"
        ? "idle"
        : status
      : "unavailable",
    errorReason,
    durationMs,
    draft,
    objectUrl,
    levels,
    isPlaying,
    playbackProgress,
    start,
    cancel,
    stop,
    discard,
    rerecord,
    togglePlayback,
    clearError,
  };
}
