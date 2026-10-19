import { Activity } from "lucide-react";
import { useOperatorSession } from "./OperatorSessionContext";
import { formatDurationHms } from "./runTimeline";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";
import { useWorkCenterActivity } from "./useWorkCenterActivity";

type Props = {
  token: string;
  branch: string;
  workCenter: string;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  onOpen: () => void;
};

/**
 * Acesso compacto à Atividade do posto (Etapa 3): faixa discreta na tela da
 * fila, sempre presente para o CT selecionado — mesmo sem operações. Um
 * toque abre o histórico diário MES; os estados especiais ficam na página.
 */
export function PostActivityCard({
  token,
  branch,
  workCenter,
  runRealtimeEvent,
  realtimeConnected,
  onOpen,
}: Props) {
  const { session, status, invalidate } = useOperatorSession();
  const { data, error, loading } = useWorkCenterActivity({
    token,
    sessionToken: session?.sessionToken ?? null,
    branch,
    workCenter,
    runRealtimeEvent,
    realtimeConnected,
    onAuthError: invalidate,
  });

  let hint: string;
  if (status === "restoring") {
    hint = "Restaurando sessão…";
  } else if (!session) {
    hint = "Identifique-se para ver paradas e produção de hoje";
  } else if (loading && !data) {
    hint = "Carregando atividade…";
  } else if (error) {
    hint = "Atividade indisponível no momento";
  } else if (!data) {
    hint = "Ver produção e paradas de hoje";
  } else if (data.source === "totvs") {
    hint = "Este posto não utiliza o histórico MES";
  } else if (data.items.length === 0) {
    hint = "Sem registros MES hoje";
  } else {
    const { stoppedSeconds, stopCount, pendingReasonCount } = data.summary;
    const parts = [`Parado ${formatDurationHms(stoppedSeconds)}`];
    parts.push(`${stopCount} ${stopCount === 1 ? "parada" : "paradas"}`);
    if (pendingReasonCount > 0) {
      parts.push(`${pendingReasonCount} sem motivo`);
    }
    hint = parts.join(" · ");
  }

  return (
    <button
      type="button"
      className="pcp-pub-activity-card"
      onClick={onOpen}
      aria-label={`Atividade do posto. ${hint}`}
    >
      <span className="pcp-pub-activity-card__icon" aria-hidden="true">
        <Activity size={20} strokeWidth={2.2} />
      </span>
      <span className="pcp-pub-activity-card__body">
        <strong className="pcp-pub-activity-card__title">Atividade do posto</strong>
        <span className="pcp-pub-activity-card__hint">{hint}</span>
      </span>
      {data?.source === "mes" && data.summary.pendingReasonCount > 0 ? (
        <span
          className="pcp-pub-activity-card__badge"
          aria-label={`${data.summary.pendingReasonCount} parada(s) sem motivo`}
        >
          {data.summary.pendingReasonCount}
        </span>
      ) : null}
    </button>
  );
}
