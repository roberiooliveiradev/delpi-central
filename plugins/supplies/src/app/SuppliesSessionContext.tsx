import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getCapabilities, type SuppliesCapabilityFlags } from "../api/capabilities";
import { getPreferences, type SuppliesPreferences } from "../api/preferences";

export type SuppliesSessionState = {
  loading: boolean;
  error: string | null;
  forbidden: boolean;
  userId: string | null;
  displayName: string | null;
  capabilities: SuppliesCapabilityFlags;
  allowedUnits: string[];
  preferences: SuppliesPreferences | null;
  reload: () => Promise<void>;
};

const EMPTY_CAPS: SuppliesCapabilityFlags = {
  portal: false,
  purchaseRequests: false,
  operations: false,
  analytics: false,
  administration: false,
  viewAll: false,
  export: false,
};

const SessionContext = createContext<SuppliesSessionState | null>(null);

export function SuppliesSessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Omit<SuppliesSessionState, "reload">>({
    loading: true,
    error: null,
    forbidden: false,
    userId: null,
    displayName: null,
    capabilities: EMPTY_CAPS,
    allowedUnits: [],
    preferences: null,
  });

  const load = useCallback(async (signal?: AbortSignal) => {
    const [caps, preferences] = await Promise.all([
      getCapabilities(signal),
      getPreferences(signal),
    ]);
    if (signal?.aborted) return;
    setState({
      loading: false,
      error: null,
      forbidden: !caps.capabilities.portal,
      userId: caps.userId || null,
      displayName: null,
      capabilities: caps.capabilities,
      allowedUnits: caps.allowedUnits,
      preferences,
    });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal).catch((err: unknown) => {
      if (controller.signal.aborted) return;
      const message = err instanceof Error ? err.message : "Falha ao carregar sessão";
      const forbidden = /403|forbidden/i.test(message);
      setState({
        loading: false,
        error: forbidden ? null : message,
        forbidden,
        userId: null,
        displayName: null,
        capabilities: EMPTY_CAPS,
        allowedUnits: [],
        preferences: null,
      });
    });
    return () => controller.abort();
  }, [load]);

  const reload = useCallback(async () => {
    await load();
  }, [load]);

  const value = useMemo(() => ({ ...state, reload }), [state, reload]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSuppliesSession(): SuppliesSessionState {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSuppliesSession must be used within SuppliesSessionProvider");
  }
  return ctx;
}
