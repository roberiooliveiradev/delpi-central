import { SectionCard, StatusBadge, SectionHintLabel } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

import {
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialLoadingCard,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ProductFactoryStatusData } from "../types/productionExtras";
import { displayApiScalar } from "../utils/displayApiScalar";
import { formatQuantity } from "../utils/format";

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

type ChipProps = {
  label: string;
  hint: string;
  children: ReactNode;
};

function FactoryChip({ label, hint, children }: ChipProps) {
  return (
    <div className="cm-open-orders-detail__factory-chip" role="listitem">
      <SectionHintLabel
        label={label}
        hint={hint}
        className="cm-open-orders-detail__factory-chip-label"
      />
      {children}
    </div>
  );
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
  const indicators = data?.indicators;
  const maxPa = indicators?.max_pa_producible_from_stock;
  const limitingMp = indicators?.limiting_raw_material_code?.trim();
  const mpWithoutStock = indicators?.total_raw_materials_without_stock_for_one_pa;
  const help = CM_HELP.openOrders.detail;

  return (
    <SectionCard
      title="Status fabril do produto"
      hint={help.factoryStatus}
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
    >
      {loading && !data ? (
        <div className="cm-open-orders-detail__section-skel">
          <CommercialLoadingCard title="Carregando status fabril…" variant="panel" />
        </div>
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
              Visão integrada PA/PI, produção e expedição do código desta linha (filial da linha).
            </p>
          </div>
          <div className="cm-open-orders-detail__factory-chips" role="list">
            <FactoryChip label="PA iniciada" hint={help.factoryPaStarted}>
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={paStarted}
                variant={ynTone(paStarted)}
              />
            </FactoryChip>
            <FactoryChip label="PI iniciada" hint={help.factoryPiStarted}>
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                label={piStarted}
                variant={ynTone(piStarted)}
              />
            </FactoryChip>
            <FactoryChip label="OPs PA / PI" hint={help.factoryOpsPaPi}>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.production?.summary?.total_pa_orders)} /{" "}
                {displayApiScalar(data.production?.summary?.total_pi_orders)}
              </strong>
            </FactoryChip>
            <FactoryChip label="Expedido" hint={help.factoryShipped}>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.shipping?.summary?.total_shipped_quantity)}
              </strong>
            </FactoryChip>
            <FactoryChip label="Perda inspeção" hint={help.factoryInspectionLoss}>
              <strong className="cm-open-orders-detail__factory-chip-value">
                {displayApiScalar(data.shipping?.summary?.total_inspection_loss_quantity)}
              </strong>
            </FactoryChip>
            {maxPa != null && Number.isFinite(Number(maxPa)) ? (
              <FactoryChip label="PA produzível (MP)" hint={help.factoryMpPa}>
                <strong className="cm-open-orders-detail__factory-chip-value">
                  {formatQuantity(Number(maxPa))}
                </strong>
              </FactoryChip>
            ) : null}
            {limitingMp ? (
              <FactoryChip label="MP limitante" hint={help.factoryMpLimiting}>
                <strong className="cm-open-orders-detail__factory-chip-value">{limitingMp}</strong>
              </FactoryChip>
            ) : null}
            {mpWithoutStock != null && Number(mpWithoutStock) > 0 ? (
              <FactoryChip label="MPs sem estoque p/ 1 PA" hint={help.factoryMpWithoutStock}>
                <strong className="cm-open-orders-detail__factory-chip-value">
                  {formatQuantity(Number(mpWithoutStock))}
                </strong>
              </FactoryChip>
            ) : null}
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
