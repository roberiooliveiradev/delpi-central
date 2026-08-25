import { useCallback, useMemo, useState } from "react";

import {
  parsePlaybackMode,
  resolvePlaybackMode,
  type PlaybackMode,
} from "./playbackMode";

const SESSION_KEY_PREFIX = "delpi-tv-playback-mode:";

function readQueryMode(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return new URL(window.location.href).searchParams.get("mode");
  } catch {
    return null;
  }
}

function readSessionMode(storageKey: string): string | null {
  if (typeof sessionStorage === "undefined") return null;
  try {
    return sessionStorage.getItem(storageKey);
  } catch {
    return null;
  }
}

function writeSessionMode(storageKey: string, mode: PlaybackMode): void {
  try {
    sessionStorage.setItem(storageKey, mode);
  } catch {
    /* WebView sem sessionStorage */
  }
}

function syncModeQueryParam(mode: PlaybackMode): void {
  if (typeof window === "undefined") return;
  try {
    const url = new URL(window.location.href);
    url.searchParams.set("mode", mode);
    window.history.replaceState(window.history.state, "", url.toString());
  } catch {
    /* ignore */
  }
}

export type UseSessionPlaybackModeOptions = {
  /** Token público ou playlistId — escopo da trava de sessão. */
  scopeKey: string;
  /** Default persistido na playlist (payload). */
  playlistMode?: string | null;
};

/**
 * Resolve modo efetivo (URL → sessão → playlist) e permite override de sessão
 * sem PATCH na API. Atualiza `?mode=` via replaceState.
 */
export function useSessionPlaybackMode({
  scopeKey,
  playlistMode = null,
}: UseSessionPlaybackModeOptions): {
  playbackMode: PlaybackMode;
  setPlaybackMode: (mode: PlaybackMode) => void;
  autoAdvance: boolean;
} {
  const storageKey = `${SESSION_KEY_PREFIX}${scopeKey || "default"}`;

  const [sessionMode, setSessionMode] = useState<PlaybackMode | null>(() => {
    const fromQuery = parsePlaybackMode(readQueryMode());
    if (fromQuery) {
      writeSessionMode(storageKey, fromQuery);
      return fromQuery;
    }
    return parsePlaybackMode(readSessionMode(storageKey));
  });

  const playbackMode = useMemo(
    () =>
      resolvePlaybackMode({
        queryMode: null,
        sessionMode,
        playlistMode,
      }),
    [sessionMode, playlistMode],
  );

  const setPlaybackMode = useCallback(
    (mode: PlaybackMode) => {
      writeSessionMode(storageKey, mode);
      setSessionMode(mode);
      syncModeQueryParam(mode);
    },
    [storageKey],
  );

  return {
    playbackMode,
    setPlaybackMode,
    autoAdvance: playbackMode === "presentation",
  };
}
