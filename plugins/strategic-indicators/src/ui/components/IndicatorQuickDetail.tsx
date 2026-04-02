import type { IndicatorAnalyticsItem } from "../../data/mocks/indicatorsMock";
import { StatusBadge } from "./StatusBadge";

type IndicatorQuickDetailProps = {
  indicator: IndicatorAnalyticsItem | null;
};

function getStatusLabel(status: IndicatorAnalyticsItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

export function IndicatorQuickDetail({
  indicator,
}: IndicatorQuickDetailProps) {
  if (!indicator) {
    return (
      <div className="si-indicator-quick-detail si-indicator-quick-detail--empty">
        Selecione um indicador na tabela para visualizar o detalhe rápido.
      </div>
    );
  }

  return (
    <aside className="si-indicator-quick-detail">
      <div className="si-indicator-quick-detail__header">
        <div>
          <p className="si-indicator-quick-detail__eyebrow">
            Detalhe rápido do indicador
          </p>
          <h3 className="si-indicator-quick-detail__title">
            {indicator.indicatorName}
          </h3>
        </div>

        <StatusBadge
          label={getStatusLabel(indicator.status)}
          variant={indicator.status}
        />
      </div>

      <div className="si-indicator-quick-detail__meta">
        <div className="si-indicator-quick-detail__meta-item">
          <span>Departamento</span>
          <strong>{indicator.departmentName}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Peso interno</span>
          <strong>{indicator.weightPct}%</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Meta 2026</span>
          <strong>{indicator.goal2026}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Nota simulada</span>
          <strong>{indicator.simulatedScore.toFixed(1)}</strong>
        </div>
      </div>

      <div className="si-indicator-quick-detail__body">
        <span className="si-indicator-quick-detail__body-label">
          Leitura estratégica
        </span>
        <p>{indicator.strategicDescription}</p>
      </div>
    </aside>
  );
}