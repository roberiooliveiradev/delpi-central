import { SectionCard, StatusBadge } from "@delpi/plugin-ui/index";

import {
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialLoadingCard,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductFactoryStatusData } from "../types/productionExtras";
import { displayApiScalar } from "../utils/displayApiScalar";

type OpenOrdersFactoryStatusStripProps = {
  loading: boolean;
  data: ProductFactoryStatusData | null;
  forbidden: boolean;
  error: string | null;
};

function factoryTone(
  status: string,
): "neutral" | "info" | "success" | "warning" | "danger" {
  const upper = status.toUpperCase();
  if (upper.includes("FINALIZ") || upper.includes("LIBERADO") || upper.includes("EXPEDI")) {
    return "success";
  }
  if (upper.includes("NÃO INICI") || upper.includes("NAO INICI") || upper.includes("ABERTA")) {
    return "warning";
  }
  if (upper.includes("ATRAS") || upper.includes("BLOQ")) return "danger";
  return "info";
}

function ynTone(value: string): "success" | "warning" | "neutral" {
  const upper = value.toUpperCase();
  if (upper === "SIM" || upper === "S" || upper === "TRUE") return "success";
  if (upper === "NÃO" || upper === "NAO" || upper === "N" || upper === "FALSE") return "warning";
  return "neutral";
}

export function OpenOrdersFactoryStatusStrip({
  loading,
  data,
  forbidden,
  error,
}: OpenOrdersFactoryStatusStripProps) {
  if (forbidden) return null;

  const statusLabel = displayApiScalar(data?.factory_status);
  const paStarted = displayApiScalar(data?.production?.summary?.pa_production_started);
  const piStarted = displayApiScalar(data?.production?.summary?.pi_production_started);

  return (
    <SectionCard
      title="Status fabril do produto"
      hint={CM_HELP.openOrders.detail.factoryStatus}
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
    >
      {loading && !data ? (
        <CommercialLoadingCard title="Carregando status fabril…" variant="panel" />
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
      {!loading && !data && !error ? (
        <p className="cm-open-orders-detail__muted">Status fabril indisponível para este produto.</p>
      ) : null}
      {data ? (
        <div className="cm-open-orders-detail__factory">
          <div className="cm-open-orders-detail__factory-hero">
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={statusLabel}
              variant={factoryTone(statusLabel)}
            />
            <p className="cm-open-orders-detail__muted">
              Visão integrada PA/PI, produção e expedição do código desta linha.
            </p>
          </div>
          <div className="cm-open-orders-detail__factory-chips" role="list">
            <div className="cm-open-orders-detail__factory-chip" role="listitem">
              <span className="cm-open-orders-detail__factory-chip-label">PA iniciada</span>
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={paStarted}
                variant={ynTone(paStarted)}
              />
            </div>
            <div className="cm-open-orders-detail__factory-chip" role="listitem">
              <span className="cm-open-orders-detail__factory-chip-label">PI iniciada</span>
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={piStarted}
                variant={ynTone(piStarted)}
              />
            </div>
            <div className="cm-open-orders-detail__factory-chip" role="listitem">
              <span className="cm-open-orders-detail__factory-chip-label">OPs PA / PI</span>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.production?.summary?.total_pa_orders)} /{" "}
                {displayApiScalar(data.production?.summary?.total_pi_orders)}
              </strong>
            </div>
            <div className="cm-open-orders-detail__factory-chip" role="listitem">
              <span className="cm-open-orders-detail__factory-chip-label">Expedido</span>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.shipping?.summary?.total_shipped_quantity)}
              </strong>
            </div>
            <div className="cm-open-orders-detail__factory-chip" role="listitem">
              <span className="cm-open-orders-detail__factory-chip-label">Perda inspeção</span>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.shipping?.summary?.total_inspection_loss_quantity)}
              </strong>
            </div>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
