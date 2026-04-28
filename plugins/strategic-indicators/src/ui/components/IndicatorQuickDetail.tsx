import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { StatusBadge } from "./StatusBadge";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
} from "../presentation/labels";
import {
  formatIndicatorGoalValue,
  formatIndicatorValue,
} from "../shared/indicatorValueFormatter";

type IndicatorQuickDetailProps = {
  indicator: IndicatorAnalyticsViewItem | null;
  competence?: string | null;
};

function getStatusLabel(status: IndicatorAnalyticsViewItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

export function IndicatorQuickDetail({
  indicator,
  competence,
}: IndicatorQuickDetailProps) {
  if (!indicator) {
    return (
      <div className="si-indicator-quick-detail si-indicator-quick-detail--empty">
        Selecione um indicador na tabela para visualizar o detalhe rápido.
      </div>
    );
  }

  const valueFormat = {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };

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
          <span>Meta</span>
          <strong>{formatIndicatorGoalValue(indicator, competence)}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Periodicidade</span>
          <strong>{getGoalPeriodicityLabel(indicator.goalPeriodicity)}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Modo da meta</span>
          <strong>{getGoalModeLabel(indicator.goalMode)}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Direção</span>
          <strong>
            {getPerformanceDirectionLabel(indicator.performanceDirection)}
          </strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Nota atual</span>
          <strong>{indicator.score.toFixed(1)}</strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Valor atual</span>
          <strong>
            {formatIndicatorValue(indicator.currentValue, valueFormat)}
          </strong>
        </div>

        <div className="si-indicator-quick-detail__meta-item">
          <span>Gap</span>
          <strong>
            {formatIndicatorValue(indicator.gap, valueFormat, {
              signed: true,
            })}
          </strong>
        </div>

        {indicator.goalMode === "monthly_curve" ? (
          <div className="si-indicator-quick-detail__meta-item">
            <span>Curva mensal</span>
            <strong>
              {indicator.monthlyTargets.length} meses parametrizados
            </strong>
          </div>
        ) : null}
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