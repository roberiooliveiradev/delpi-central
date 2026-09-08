import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getCapabilities, type SuppliesCapabilityFlags } from "../api/capabilities";
import { getPreferences, type SuppliesPreferences } from "../api/preferences";

export type SuppliesSessionState = {
  loading: boolean;
  error: string | null;
  forbidden: boolean;
  capabilities: SuppliesCapabilityFlags;
  allowedUnits: string[];
  preferences: SuppliesPreferences | null;
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
  const [state, setState] = useState<SuppliesSessionState>({
    loading: true,
    error: null,
    forbidden: false,
    capabilities: EMPTY_CAPS,
    allowedUnits: [],
    preferences: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([getCapabilities(controller.signal), getPreferences(controller.signal)])
      .then(([caps, preferences]) => {
        setState({
          loading: false,
          error: null,
          forbidden: !caps.capabilities.portal,
          capabilities: caps.capabilities,
          allowedUnits: caps.allowedUnits,
          preferences,
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : "Falha ao carregar sessão";
        const forbidden = /403|forbidden/i.test(message);
        setState({
          loading: false,
          error: forbidden ? null : message,
          forbidden,
          capabilities: EMPTY_CAPS,
          allowedUnits: [],
          preferences: null,
        });
      });
    return () => controller.abort();
  }, []);

  const value = useMemo(() => state, [state]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSuppliesSession(): SuppliesSessionState {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSuppliesSession must be used within SuppliesSessionProvider");
  }
  return ctx;
}
