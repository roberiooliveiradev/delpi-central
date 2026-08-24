import { useEffect, useState } from "react";

export type UsePersistedBooleanOptions = {
  storageKey: string;
  defaultValue?: boolean;
  /** When false, does not read/write localStorage (default true). */
  enabled?: boolean;
};

function readStored(storageKey: string): boolean | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (raw === "1") return true;
    if (raw === "0") return false;
  } catch {
    /* ignore */
  }
  return null;
}

/**
 * Persist a boolean flag in localStorage as `"1"` / `"0"`.
 */
export function usePersistedBoolean(options: UsePersistedBooleanOptions) {
  const { storageKey, defaultValue = false, enabled = true } = options;

  const [value, setValue] = useState<boolean>(() => {
    if (!enabled) return defaultValue;
    return readStored(storageKey) ?? defaultValue;
  });

  useEffect(() => {
    if (!enabled) return;
    try {
      window.localStorage.setItem(storageKey, value ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [enabled, storageKey, value]);

  return { value, setValue };
}

export type UsePersistedBooleanResult = ReturnType<typeof usePersistedBoolean>;
