import { useEffect, useState } from "react";

export type SearchMode = "tool" | "part";

export type UsePersistedSearchModeOptions = {
  storageKey: string;
  defaultMode?: SearchMode;
  /** Quando false, não lê/grava localStorage (default true). */
  enabled?: boolean;
};

export function isSearchMode(value: string): value is SearchMode {
  return value === "tool" || value === "part";
}

export function readStoredSearchMode(storageKey: string): SearchMode | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw && isSearchMode(raw)) return raw;
  } catch {
    /* ignore */
  }
  return null;
}

export function usePersistedSearchMode(options: UsePersistedSearchModeOptions) {
  const { storageKey, defaultMode = "tool", enabled = true } = options;

  const [mode, setMode] = useState<SearchMode>(() => {
    if (!enabled) return defaultMode;
    return readStoredSearchMode(storageKey) ?? defaultMode;
  });

  useEffect(() => {
    if (!enabled) return;
    try {
      window.localStorage.setItem(storageKey, mode);
    } catch {
      /* ignore */
    }
  }, [enabled, mode, storageKey]);

  return {
    mode,
    setMode,
  };
}

export type UsePersistedSearchModeResult = ReturnType<typeof usePersistedSearchMode>;
