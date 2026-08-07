import { useEffect, useState } from "react";

export type OpenOrdersLayoutMode = "table" | "cards";

const STORAGE_KEY = "commercial:open-orders:layout";

function readStored(): OpenOrdersLayoutMode | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "table" || raw === "cards") return raw;
  } catch {
    /* ignore */
  }
  return null;
}

function defaultLayout(): OpenOrdersLayoutMode {
  if (typeof window === "undefined") return "table";
  if (window.matchMedia("(max-width: 768px)").matches) return "cards";
  return "table";
}

export function useOpenOrdersLayout() {
  const [layout, setLayoutState] = useState<OpenOrdersLayoutMode>(() => readStored() ?? defaultLayout());

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, layout);
    } catch {
      /* ignore */
    }
  }, [layout]);

  return {
    layout,
    setLayout: setLayoutState,
  };
}
