import { useEffect, useState } from "react";

export type PersistedViewLayoutMode = "table" | "cards";

export type UsePersistedViewLayoutOptions = {
  storageKey: string;
  /** Default desktop. Mobile (≤768px) usa cards quando não há valor persistido. */
  defaultMode?: PersistedViewLayoutMode;
  mobileMaxWidthPx?: number;
};

function readStored(storageKey: string): PersistedViewLayoutMode | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw === "table" || raw === "cards") return raw;
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
  if (window.matchMedia(`(max-width: ${mobileMaxWidthPx}px)`).matches) {
    return "cards";
  }
  return defaultMode;
}

export function usePersistedViewLayout(options: UsePersistedViewLayoutOptions) {
  const {
    storageKey,
    defaultMode = "table",
    mobileMaxWidthPx = 768,
  } = options;

  const [layout, setLayout] = useState<PersistedViewLayoutMode>(
    () => readStored(storageKey) ?? resolveDefaultLayout(defaultMode, mobileMaxWidthPx),
  );

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, layout);
    } catch {
      /* ignore */
    }
  }, [layout, storageKey]);

  return {
    layout,
    setLayout,
  };
}

export type UsePersistedViewLayoutResult = ReturnType<typeof usePersistedViewLayout>;
