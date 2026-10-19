import type { ReactNode } from "react";
import { CockpitActivityContext } from "./CockpitActivityContext";
import { useOperatorSession } from "./OperatorSessionContext";
import { useWorkCenterActivity } from "./useWorkCenterActivity";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

/**
 * Provider da leitura diária MES compartilhada (Etapa 4). Vive DENTRO do
 * OperatorSessionProvider: a sessão continua sendo autoridade única — um
 * único GET por escopo alimenta cartão, indicadores e página de atividade.
 */
export function CockpitActivityProvider({
  token,
  branch,
  workCenter,
  runRealtimeEvent,
  realtimeConnected,
  children,
}: {
  token: string;
  branch: string;
  workCenter: string | null;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  children: ReactNode;
}) {
  const { session, invalidate } = useOperatorSession();
  const activity = useWorkCenterActivity({
    token,
    sessionToken: session?.sessionToken ?? null,
    branch,
    workCenter,
    runRealtimeEvent,
    realtimeConnected,
    onAuthError: invalidate,
  });
  return (
    <CockpitActivityContext.Provider value={activity}>
      {children}
    </CockpitActivityContext.Provider>
  );
}
