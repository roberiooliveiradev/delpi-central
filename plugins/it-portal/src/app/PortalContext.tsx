/**
 * Contexto do portal: capabilities efetivas (decididas pela BFF) e avisos.
 * A UI só esconde/mostra controles — a autorização continua no backend.
 */
import { useQuery } from "@tanstack/react-query";
import { useFloatingNotices } from "@delpi/plugin-ui/index";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";

import { ApiError } from "../api/httpClient";
import { itPortalApi, type Capabilities } from "../api/itPortalApi";
import { NOTICE_CONTENT } from "../content/labels";
import { ItpNoticeStack } from "./itPortalUi";
import { queryKeys } from "./queryKeys";

type PortalContextValue = {
  basePath: string;
  capabilities: Capabilities | null;
  capabilitiesLoading: boolean;
  capabilitiesError: ApiError | null;
  refetchCapabilities: () => void;
  notifySuccess: (message: string) => void;
  notifyError: (error: unknown) => void;
};

const PortalContext = createContext<PortalContextValue | null>(null);

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  return new ApiError(0, "Erro inesperado. Tente novamente.", "unexpected_error");
}

export function PortalProvider({ basePath, children }: { basePath: string; children: ReactNode }) {
  const notices = useFloatingNotices();
  const capabilitiesQuery = useQuery({
    queryKey: queryKeys.capabilities,
    queryFn: ({ signal }) => itPortalApi.capabilities(signal),
    staleTime: 60_000,
    retry: false,
  });

  const { push } = notices;
  const notifySuccess = useCallback(
    (message: string) => push({ variant: "success", title: NOTICE_CONTENT.successTitle, message }),
    [push],
  );
  const notifyError = useCallback(
    (error: unknown) =>
      push({ variant: "error", title: NOTICE_CONTENT.errorTitle, message: toApiError(error).message }),
    [push],
  );

  const { refetch, data, isPending, error } = capabilitiesQuery;
  const value = useMemo<PortalContextValue>(
    () => ({
      basePath,
      capabilities: data ?? null,
      capabilitiesLoading: isPending,
      capabilitiesError: error ? toApiError(error) : null,
      refetchCapabilities: () => void refetch(),
      notifySuccess,
      notifyError,
    }),
    [basePath, data, isPending, error, refetch, notifySuccess, notifyError],
  );

  return (
    <PortalContext.Provider value={value}>
      {children}
      <ItpNoticeStack items={notices.items} onDismiss={notices.dismiss} />
    </PortalContext.Provider>
  );
}

export function usePortal(): PortalContextValue {
  const context = useContext(PortalContext);
  if (!context) throw new Error("usePortal requires PortalProvider");
  return context;
}
