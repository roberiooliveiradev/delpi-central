import {
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialHorizontalTimeline,
  CommercialInlineMeter,
  CommercialLoadingCard,
  UI_PREFIX,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { OpAllocationEntry } from "../types/opForecast";
import type { OpExtrasBundle } from "../hooks/useOpenOrdersLineDetailExtras";
import { formatDisplayDate, resolveOpVsPedidoPrazo } from "../utils/dates";
import { displayApiScalar } from "../utils/displayApiScalar";
import { formatQuantity } from "../utils/format";
import { buildOpHorizontalTimeline, buildOpTimelineEvents } from "../utils/opTimeline";
import {
  formatOtdStatusLabel,
  otdStatusBadgeVariant,
} from "../utils/productionOtdLink";
import { SectionCard, SegmentToggle, StatusBadge, SectionHintLabel } from "@delpi/plugin-ui/index";
import { useMemo } from "react";
import { OpenOrdersOtdPiPanel } from "./OpenOrdersOtdPiPanel";

type OpenOrdersOpProgressBlockProps = {
  ops: OpAllocationEntry[];
  selectedOp: string;
  onSelectOp: (numeroOp: string) => void;
  orderDeliveryDate: string | null;
  branch?: string | null;
  extrasByOp: Record<string, OpExtrasBundle>;
  loadingExtras: boolean;
  opsPrefetchTruncated?: number;
};

export function OpenOrdersOpProgressBlock({
  ops,
  selectedOp,
  onSelectOp,
  orderDeliveryDate,
  branch,
  extrasByOp,
  loadingExtras,
  opsPrefetchTruncated = 0,
}: OpenOrdersOpProgressBlockProps) {
  const current = useMemo(
    () => ops.find((op) => op.numero_op === selectedOp) ?? ops[0] ?? null,
    [ops, selectedOp],
  );

  if (!current) {
    return (
      <SectionCard
        title="Produção / OPs"
        hint={CM_HELP.openOrders.detail.opsTable}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <p className="cm-open-orders-drawer__empty">Nenhuma OP alocada para esta linha.</p>
      </SectionCard>
    );
  }

  const extras = extrasByOp[current.numero_op];
  const order = extras?.byOp?.order;
  const planned = Math.max(0, order?.planned_qty ?? current.quantidade_op ?? 0);
  const produced = Math.max(
    0,
    order?.produced_qty ?? current.quantidade_produzida ?? 0,
  );
  const progressRatio = planned > 0 ? Math.min(1, produced / planned) : 0;
  const timelineItems = buildOpTimelineEvents({
    op: current,
    orderDeliveryDate,
    byOp: extras?.byOp ?? null,
    appointments: extras?.appointments ?? [],
  });
  const horizontalPoints = buildOpHorizontalTimeline(timelineItems);
  const appointments = (extras?.appointments ?? []).slice(0, 5);

  const prazo = resolveOpVsPedidoPrazo(
    order?.due_date ?? current.data_fim_prevista_op,
    orderDeliveryDate,
  );

  return (
    <SectionCard
      title="Produção / OPs"
      hint={CM_HELP.openOrders.detail.opsTable}
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
    >
      {ops.length > 1 ? (
        <div className="cm-open-orders-detail__op-toggle">
          <SegmentToggle
            prefix={UI_PREFIX}
            size="sm"
            idPrefix="open-orders-op"
            ariaLabel="Selecionar OP"
            value={current.numero_op}
            onChange={onSelectOp}
            options={ops.map((op) => ({
              value: op.numero_op,
              label: op.numero_op,
            }))}
          />
        </div>
      ) : null}

      {opsPrefetchTruncated > 0 ? (
        <p className="cm-open-orders-detail__muted">
          +{opsPrefetchTruncated} OP(s) além do prefetch — selecione na tabela para carregar o
          detalhe.
        </p>
      ) : null}

      <div className="cm-open-orders-detail__op-card">
        <div className="cm-open-orders-detail__op-header">
          <strong>OP {current.numero_op}</strong>
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={displayApiScalar(order?.order_status, "Status —")}
            variant="neutral"
          />
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={`OTD: ${formatOtdStatusLabel(order?.otd_status)}`}
            variant={otdStatusBadgeVariant(order?.otd_status)}
          />
          {displayApiScalar(order?.warehouse || current.armazem, "") ? (
            <span>Armazém {displayApiScalar(order?.warehouse || current.armazem)}</span>
          ) : null}
          <StatusBadge
            classNames={cmStatusBadgeClassNames}
            label={
              prazo.status === "atrasado"
                ? "Fim OP atrasado vs pedido"
                : prazo.status === "no_prazo"
                  ? "Fim OP no prazo"
                  : "Prazo OP indeterminado"
            }
            variant={
              prazo.status === "atrasado"
                ? "danger"
                : prazo.status === "no_prazo"
                  ? "success"
                  : "neutral"
            }
          />
        </div>

        <CommercialInlineMeter
          value={progressRatio}
          max={1}
          tone={progressRatio >= 1 ? "success" : progressRatio > 0 ? "warning" : "neutral"}
          size="md"
          label={`${formatQuantity(produced)} / ${formatQuantity(planned)} produzido`}
          aria-label="Progresso da OP"
        />

        <p className="cm-open-orders-detail__muted">
          Emissão {formatDisplayDate(order?.issue_date ?? current.data_emissao_op)} · Início prev.{" "}
          {formatDisplayDate(order?.planned_start_date ?? current.data_inicio_prevista_op)} · Fim
          prev. {formatDisplayDate(order?.due_date ?? current.data_fim_prevista_op)}
        </p>

        {extras?.byOp ? (
          <OpenOrdersOtdPiPanel
            productionOrder={current.numero_op}
            branch={order?.branch ?? branch}
            byOp={extras.byOp}
          />
        ) : extras?.loading ? (
          <CommercialLoadingCard title="Carregando prazo OTD…" variant="panel" />
        ) : null}

        {loadingExtras && !extras ? (
          <CommercialLoadingCard title="Carregando timeline da OP…" variant="panel" />
        ) : (
          <div className="cm-open-orders-detail__timeline-wrap">
            <SectionHintLabel
              label="Linha do tempo da OP"
              hint={CM_HELP.openOrders.detail.timeline}
              className="cm-open-orders-detail__timeline-caption"
            />
            <CommercialHorizontalTimeline
              points={horizontalPoints}
              labels={{ emptyMessage: "Sem marcos com data para esta OP." }}
              aria-label={`Linha do tempo da OP ${current.numero_op}`}
            />
          </div>
        )}

        {appointments.length > 0 ? (
          <div className="cm-open-orders-detail__appointments">
            <SectionHintLabel
              label="Apontamentos"
              hint={CM_HELP.openOrders.detail.appointments}
              className="cm-open-orders-detail__otd-pi-title"
            />
            <ul className="cm-open-orders-detail__appointments-list">
              {appointments.map((row, index) => {
                const first = row.first_date || row.appointment_date;
                const last = row.last_date || first;
                const qty = row.qty_produced ?? row.reported_quantity;
                return (
                  <li
                    key={`${row.production_order || current.numero_op}-${index}`}
                    className="cm-open-orders-detail__appointments-row"
                  >
                    <span>
                      {formatDisplayDate(first)}
                      {last && first && last !== first
                        ? ` – ${formatDisplayDate(last)}`
                        : ""}
                    </span>
                    <span className="cm-open-orders-detail__muted">
                      {Number(row.appointment_count) > 1
                        ? `${row.appointment_count} apont.`
                        : "1 apont."}
                      {row.work_center_count != null
                        ? ` · ${row.work_center_count} centro(s)`
                        : row.work_center
                          ? ` · ${row.work_center}`
                          : ""}
                    </span>
                    <strong>{formatQuantity(qty)}</strong>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        {extras?.error ? <p role="alert">{extras.error}</p> : null}
      </div>
    </SectionCard>
  );
}
