import { useCallback, useEffect, useState } from "react";

import {
  clampTableFontSize,
  DEFAULT_TABLE_FONT_SIZE,
  loadTableFontSize,
  MAX_TABLE_FONT_SIZE,
  MIN_TABLE_FONT_SIZE,
  saveTableFontSize,
} from "../utils/tableFontSize";

export function useTableFontSize() {
  const [fontSize, setFontSize] = useState(() => loadTableFontSize());

  useEffect(() => {
    saveTableFontSize(fontSize);
  }, [fontSize]);

  const increase = useCallback(() => {
    setFontSize((current) => clampTableFontSize(current + 1));
  }, []);

  const decrease = useCallback(() => {
    setFontSize((current) => clampTableFontSize(current - 1));
  }, []);

  const reset = useCallback(() => {
    setFontSize(DEFAULT_TABLE_FONT_SIZE);
  }, []);

  return {
    fontSize,
    increase,
    decrease,
    reset,
    canIncrease: fontSize < MAX_TABLE_FONT_SIZE,
    canDecrease: fontSize > MIN_TABLE_FONT_SIZE,
    isDefault: fontSize === DEFAULT_TABLE_FONT_SIZE,
  };
}

export type UseTableFontSizeResult = ReturnType<typeof useTableFontSize>;
