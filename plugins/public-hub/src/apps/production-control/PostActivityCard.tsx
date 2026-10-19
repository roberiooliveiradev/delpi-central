import { Activity } from "lucide-react";
import { useCockpitActivity } from "./CockpitActivityContext";
import { useOperatorSession } from "./OperatorSessionContext";
import { formatDurationHms } from "./runTimeline";

type Props = {
  onOpen: () => void;
};

/**
 * Acesso compacto à Atividade do posto (Etapa 3): faixa discreta na tela da
 * fila, sempre presente para o CT selecionado — mesmo sem operações. Um
 * toque abre o histórico diário MES; os estados especiais ficam na página.
 * A leitura vem do CockpitActivityProvider — um único GET por escopo,
 * compartilhado com os indicadores do cabeçalho e a página de detalhe.
 */
export function PostActivityCard({ onOpen }: Props) {
  const { session, status } = useOperatorSession();
  const { data, error, loading } = useCockpitActivity();

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
      parts.push(
        `${pendingReasonCount} ${pendingReasonCount === 1 ? "motivo pendente" : "motivos pendentes"}`,
      );
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
          aria-label={`${data.summary.pendingReasonCount} parada(s) com motivo pendente`}
        >
          {data.summary.pendingReasonCount}
        </span>
      ) : null}
    </button>
  );
}
