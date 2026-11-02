import { PauseCircle } from "lucide-react";
import { useCockpitActivity } from "./CockpitActivityContext";
import { useOperatorSession } from "./OperatorSessionContext";

type Props = {
  onOpen: () => void;
};

/**
 * Acesso compacto a «Paradas do posto»: faixa na tela da fila, sempre
 * presente para o CT selecionado. Um toque abre a lista de paradas MES do
 * dia. A leitura vem do CockpitActivityProvider — um único GET por escopo.
 */
export function PostActivityCard({ onOpen }: Props) {
  const { session, status } = useOperatorSession();
  const { data, error, loading } = useCockpitActivity();

  let hint: string;
  if (status === "restoring") {
    hint = "Restaurando sessão…";
  } else if (!session) {
    hint = "Identifique-se para ver as paradas de hoje";
  } else if (loading && !data) {
    hint = "Carregando paradas…";
  } else if (error) {
    hint = "Paradas indisponíveis no momento";
  } else if (!data) {
    hint = "Ver paradas de hoje";
  } else if (data.source === "totvs") {
    hint = "Este posto não utiliza o histórico MES";
  } else if (data.summary.stopCount === 0) {
    hint = "Sem paradas MES hoje";
  } else {
    const { stopCount, pendingReasonCount } = data.summary;
    const parts = [
      `${stopCount} ${stopCount === 1 ? "parada" : "paradas"}`,
    ];
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
      aria-label={`Paradas do posto. ${hint}`}
    >
      <span className="pcp-pub-activity-card__icon" aria-hidden="true">
        <PauseCircle size={20} strokeWidth={2.2} />
      </span>
      <span className="pcp-pub-activity-card__body">
        <strong className="pcp-pub-activity-card__title">Paradas do posto</strong>
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
