import { useEffect, useState } from "react";

/** Canonical debounce for auto-applied text filters (default 350ms). */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export const SUPPLIES_FILTER_TEXT_DEBOUNCE_MS = 350;
