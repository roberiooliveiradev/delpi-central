import { useEffect, useId, useState } from "react";
import {
  createDashboardDetailFieldGrid,
  createDashboardStatusBadge,
  createModalShell,
} from "@delpi/plugin-ui/index";

import { useConsumptionAnalysisItemDetails } from "../hooks/useConsumptionAnalysisItemDetails";
import type { ConsumptionAnalysisItem } from "../types/consumptionAnalysis";
import { formatNumberPtBr } from "../utils/formatters";
import {
  analysisQualityWarningLabel,
  analysisStatusLabel,
  analysisStatusVariant,
  formatIsoDatePtBr,
} from "../utils/safetyStockStatus";
import { ConsumptionAnalysisDetailProductSearch } from "./ConsumptionAnalysisDetailProductSearch";
import { ProductConsumptionChartsSection } from "./ProductConsumptionChartsSection";
import { SectionError } from "./SectionError";

const Modal = createModalShell({
  prefix: "ess",
  variant: "page",
  portalScopeClassName: "dashboard-estoque-seguranca",
  closeAriaLabel: "Fechar detalhe da análise de consumo",
});

const StatusBadge = createDashboardStatusBadge({ prefix: "ess" });
const DetailFields = createDashboardDetailFieldGrid({
  prefix: "ess",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});

type ConsumptionAnalysisDetailModalProps = {
  item: ConsumptionAnalysisItem | null;
  onClose: () => void;
  onNavigate?: (item: ConsumptionAnalysisItem) => void;
};

export function ConsumptionAnalysisDetailModal({
  item,
  onClose,
  onNavigate,
}: ConsumptionAnalysisDetailModalProps) {
  const open = Boolean(item);
  const calcPanelId = useId();
  const [showCalculation, setShowCalculation] = useState(false);
  const details = useConsumptionAnalysisItemDetails(
    item?.branch ?? null,
    item?.product_code ?? null,
  );
  const resolved = details.data?.item ?? item;
  const memory = details.data?.calculation_memory;
  const monthly = details.data?.monthly_consumption.items ?? [];
  const annualComparison = details.data?.annual_comparison;

  useEffect(() => {
    setShowCalculation(false);
  }, [item?.branch, item?.product_code]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={resolved?.product_code ?? "Análise"}
      headerActions={
        resolved && onNavigate ? (
          <ConsumptionAnalysisDetailProductSearch
            branch={resolved.branch}
            onNavigate={onNavigate}
          />
        ) : undefined
      }
    >
      {!resolved ? null : (
        <div className="ess-detail">
          <div className="ess-detail__section-header">
            <h2>{resolved.product_description || resolved.product_code}</h2>
            <StatusBadge
              label={analysisStatusLabel(resolved.analysis_status)}
              variant={analysisStatusVariant(resolved.analysis_status)}
            />
          </div>

          {details.loading ? (
            <p className="ess-detail__state" role="status">
              Carregando memória de cálculo e série mensal…
            </p>
          ) : null}

          {!details.loading && details.error ? (
            <SectionError
              title={details.error.title}
              message={details.error.message}
              onRetry={details.error.retryable ? details.reload : undefined}
            />
          ) : null}

          <section className="ess-detail__section" aria-label="Indicadores do item">
            <DetailFields
              fields={[
                { label: "ESTSEG atual", value: formatNumberPtBr(resolved.safety_stock) },
                {
                  label: "Sugerido",
                  value: formatNumberPtBr(resolved.suggested_safety_stock),
                  hint: "Consumo diário × dias úteis do lead time (arredondado para cima)",
                },
                {
                  label: "Diferença",
                  value: formatNumberPtBr(resolved.difference_quantity),
                },
                {
                  label: "Consumo do período",
                  value: formatNumberPtBr(resolved.period_consumption),
                },
                {
                  label: "Consumo diário",
                  value: formatNumberPtBr(resolved.average_daily_consumption),
                  hint: "Consumo do período ÷ dias úteis dos últimos 12 meses",
                },
                {
                  label: "Lead time",
                  value: `${formatNumberPtBr(resolved.lead_time_days, 0)} dias corridos`,
                  hint: "Campo BZ_PE do cadastro do produto",
                },
                {
                  label: "Lead time em dias úteis",
                  value: formatNumberPtBr(resolved.lead_time_business_days, 0),
                },
                {
                  label: "Saldo disponível",
                  value: formatNumberPtBr(resolved.available_stock),
                  hint: "Armazéns 01 + 98 + 99",
                },
                {
                  label: "Cobertura atual",
                  value:
                    resolved.coverage_business_days == null
                      ? "—"
                      : `${formatNumberPtBr(resolved.coverage_business_days)} dias úteis`,
                },
                {
                  label: "Movimentos",
                  value: String(resolved.movement_count),
                },
                {
                  label: "Primeira baixa",
                  value: formatIsoDatePtBr(resolved.first_movement_date),
                },
                {
                  label: "Última baixa",
                  value: formatIsoDatePtBr(resolved.last_movement_date),
                },
              ]}
            />
          </section>

          {memory ? (
            <section className="ess-detail__section" aria-label="Memória de cálculo">
              <div className="ess-detail__section-header">
                <h3>Como chegamos no sugerido</h3>
              </div>
              <button
                type="button"
                className="ess-btn ess-btn--secondary ess-calc-toggle"
                aria-expanded={showCalculation}
                aria-controls={calcPanelId}
                onClick={() => setShowCalculation((current) => !current)}
              >
                {showCalculation ? "Ocultar cálculo" : "Ver o Cálculo"}
              </button>
              <p className="ess-detail__hint">
                O estoque sugerido cobre o consumo médio enquanto a compra chega, com base
                no lead time cadastrado.
              </p>
              {showCalculation ? (
                <div
                  id={calcPanelId}
                  className="ess-calc-card"
                  role="region"
                  aria-label="Detalhe do cálculo"
                >
                  <pre className="ess-calc-block">
                    {`Consumo diário = ${formatNumberPtBr(memory.period_consumption)} ÷ ${formatNumberPtBr(memory.period_business_days, 0)} dias úteis
                 = ${formatNumberPtBr(memory.average_daily_consumption)}

Lead time      = ${formatNumberPtBr(memory.lead_time_days, 0)} dias corridos
                 → ${formatNumberPtBr(memory.lead_time_business_days, 0)} dias úteis

Estoque sugerido = arredondar para cima(
  ${formatNumberPtBr(memory.average_daily_consumption)} × ${formatNumberPtBr(memory.lead_time_business_days, 0)}
)
                 = ${formatNumberPtBr(memory.suggested_safety_stock)}

Comparação     = ESTSEG atual ${formatNumberPtBr(memory.current_safety_stock)}
                 vs sugerido ${formatNumberPtBr(memory.suggested_safety_stock)}`}
                  </pre>
                  <p className="ess-detail__hint">
                    Consideramos apenas baixas de produção no armazém 99, com ordem de
                    produção e tipo de movimento 999.
                  </p>
                  {memory.quality_warnings.length > 0 ? (
                    <ul className="ess-calc-warnings" aria-label="Alertas da análise">
                      {memory.quality_warnings.map((warning) => (
                        <li key={warning}>{analysisQualityWarningLabel(warning)}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ) : null}
            </section>
          ) : null}

          <ProductConsumptionChartsSection
            monthlyPoints={monthly}
            periodConsumption={resolved.period_consumption}
            annualComparison={annualComparison}
            loading={details.loading}
            resetKey={`${resolved.branch}-${resolved.product_code}`}
          />
        </div>
      )}
    </Modal>
  );
}
