import { useCallback, useEffect, useState } from "react";

import {
  clampTableFontSize,
  DEFAULT_TABLE_FONT_SIZE,
  loadTableFontSize,
  MAX_TABLE_FONT_SIZE,
  MIN_TABLE_FONT_SIZE,
  saveTableFontSize,
  type TableFontSizePreferenceOptions,
} from "../utils/tableFontSizePreferences";

export type UseTableFontSizeOptions = TableFontSizePreferenceOptions & {
  /** Quando false, não lê/grava localStorage (default true). */
  enabled?: boolean;
};

export function useTableFontSize(options: UseTableFontSizeOptions) {
  const { storageKey, legacyStorageKeys, enabled = true } = options;
  const [fontSize, setFontSize] = useState(() =>
    enabled
      ? loadTableFontSize({ storageKey, legacyStorageKeys })
      : DEFAULT_TABLE_FONT_SIZE,
  );

  useEffect(() => {
    if (!enabled) return;
    saveTableFontSize(fontSize, { storageKey });
  }, [enabled, fontSize, storageKey]);

  const increase = useCallback(() => {
    if (!enabled) return;
    setFontSize((current) => clampTableFontSize(current + 1));
  }, [enabled]);

  const decrease = useCallback(() => {
    if (!enabled) return;
    setFontSize((current) => clampTableFontSize(current - 1));
  }, [enabled]);

  const reset = useCallback(() => {
    if (!enabled) return;
    setFontSize(DEFAULT_TABLE_FONT_SIZE);
  }, [enabled]);

  return {
    fontSize,
    increase,
    decrease,
    reset,
    canIncrease: enabled && fontSize < MAX_TABLE_FONT_SIZE,
    canDecrease: enabled && fontSize > MIN_TABLE_FONT_SIZE,
    isDefault: fontSize === DEFAULT_TABLE_FONT_SIZE,
  };
}

export type UseTableFontSizeResult = ReturnType<typeof useTableFontSize>;
