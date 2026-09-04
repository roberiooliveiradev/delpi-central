import { useCallback, useEffect, useState } from "react";

import {
  DEFAULT_QUANTITY_DISPLAY_MODE,
  QUANTITY_DISPLAY_STORAGE_KEY,
  normalizeQuantityDisplayMode,
  type QuantityDisplayMode,
} from "../utils/displayQuantity";

function readStoredMode(): QuantityDisplayMode {
  if (typeof window === "undefined") return DEFAULT_QUANTITY_DISPLAY_MODE;
  try {
    return normalizeQuantityDisplayMode(
      window.localStorage.getItem(QUANTITY_DISPLAY_STORAGE_KEY),
    );
  } catch {
    return DEFAULT_QUANTITY_DISPLAY_MODE;
  }
}

/** Shared UI preference: milheiro (catalog) vs pieces for UM=MI only. */
export function useQuantityDisplayMode() {
  const [mode, setModeState] = useState<QuantityDisplayMode>(
    DEFAULT_QUANTITY_DISPLAY_MODE,
  );

  useEffect(() => {
    setModeState(readStoredMode());
  }, []);

  const setMode = useCallback((next: QuantityDisplayMode) => {
    const normalized = normalizeQuantityDisplayMode(next);
    setModeState(normalized);
    try {
      window.localStorage.setItem(QUANTITY_DISPLAY_STORAGE_KEY, normalized);
    } catch {
      /* ignore */
    }
  }, []);

  return { mode, setMode };
}
