import { useEffect, useState } from "react";

/**
 * Debounces a fast-changing value (ex.: search input) so consumers only
 * react after the user pauses. The returned value trails `value` by
 * `delayMs`; timers are cleaned up on every change/unmount.
 */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}
