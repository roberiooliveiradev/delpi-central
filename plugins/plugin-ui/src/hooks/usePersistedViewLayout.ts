import { useEffect, useState } from "react";

export type PersistedViewLayoutMode = "table" | "cards" | "board";

export type UsePersistedViewLayoutOptions = {
  storageKey: string;
  /** Default desktop. Mobile (≤768px) usa cards quando não há valor persistido. */
  defaultMode?: PersistedViewLayoutMode;
  mobileMaxWidthPx?: number;
  /** Quando false, não lê/grava localStorage (default true). */
  enabled?: boolean;
};

function readStored(storageKey: string): PersistedViewLayoutMode | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw === "table" || raw === "cards" || raw === "board") return raw;
  } catch {
    /* ignore */
  }
  return null;
}

function resolveDefaultLayout(
  defaultMode: PersistedViewLayoutMode,
  mobileMaxWidthPx: number,
): PersistedViewLayoutMode {
  if (typeof window === "undefined") return defaultMode;
  const matchMedia = window.matchMedia?.bind(window);
  if (typeof matchMedia !== "function") return defaultMode;
  if (matchMedia(`(max-width: ${mobileMaxWidthPx}px)`).matches) {
    return "cards";
  }
  return defaultMode;
}

export function usePersistedViewLayout(options: UsePersistedViewLayoutOptions) {
  const {
    storageKey,
    defaultMode = "table",
    mobileMaxWidthPx = 768,
    enabled = true,
  } = options;

  const [layout, setLayout] = useState<PersistedViewLayoutMode>(() => {
    if (!enabled) return defaultMode;
    return readStored(storageKey) ?? resolveDefaultLayout(defaultMode, mobileMaxWidthPx);
  });

  useEffect(() => {
    if (!enabled) return;
    try {
      window.localStorage.setItem(storageKey, layout);
    } catch {
      /* ignore */
    }
  }, [enabled, layout, storageKey]);

  return {
    layout,
    setLayout,
  };
}

export type UsePersistedViewLayoutResult = ReturnType<typeof usePersistedViewLayout>;
