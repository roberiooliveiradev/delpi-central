import type { HorizontalTimelineTone } from "@delpi/plugin-ui/index";
import type { OpAllocationEntry } from "../types/opForecast";
import type { ProductionAppointmentItem, ProductionOrderByOpData } from "../types/productionExtras";
import { formatDisplayDate, resolveOpVsPedidoPrazo } from "./dates";

export type OpTimelineTone = "default" | "danger" | "warning" | "success" | "info";

function toHorizontalTone(tone: OpTimelineTone | undefined): HorizontalTimelineTone {
  if (!tone || tone === "default") return "neutral";
  return tone;
}

export type OpTimelineItem = {
  id: string;
  title: string;
  occurredAt?: string | null;
  timeLabel?: string;
  detail?: string;
  tone?: OpTimelineTone;
};

export type OpTimelineLabels = {
  emission: string;
  plannedStart: string;
  orderDelivery: string;
  plannedEnd: string;
  appointment: string;
  appointmentsMany: (count: number) => string;
  finishReal: string;
};

export const DEFAULT_OP_TIMELINE_LABELS: OpTimelineLabels = {
  emission: "Emissão da OP",
  plannedStart: "Início previsto",
  orderDelivery: "Entrega do pedido",
  plannedEnd: "Fim previsto da OP",
  appointment: "Apontamento",
  appointmentsMany: (count) => `${count} apontamentos`,
  finishReal: "Fim real",
};

export type BuildOpTimelineInput = {
  op: OpAllocationEntry;
  orderDeliveryDate?: string | null;
  byOp?: ProductionOrderByOpData | null;
  appointments?: ProductionAppointmentItem[] | null;
  labels?: Partial<OpTimelineLabels>;
};

function sortKey(iso: string | null | undefined): string {
  if (!iso) return "";
  const match = String(iso).match(/^(\d{4}-\d{2}-\d{2})/);
  return match?.[1] ?? String(iso);
}

function plannedEndTone(
  dataFim: string | null | undefined,
  orderDelivery: string | null | undefined,
): OpTimelineTone {
  const prazo = resolveOpVsPedidoPrazo(dataFim, orderDelivery);
  if (prazo.status === "atrasado") return "danger";
  if (prazo.status === "no_prazo") return "success";
  return "warning";
}

function orderDeliveryTone(orderDelivery: string | null | undefined): OpTimelineTone {
  if (!orderDelivery) return "default";
  const iso = sortKey(orderDelivery);
  const today = new Date();
  const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  if (iso && iso < todayIso) return "warning";
  return "default";
}

/**
 * Monta eventos da timeline fabril da OP (marcos SC2 + pedido + apontamentos).
 * Datas nulas são omitidas — não gera placeholder «—».
 */
export function buildOpTimelineEvents(input: BuildOpTimelineInput): OpTimelineItem[] {
  const labels: OpTimelineLabels = { ...DEFAULT_OP_TIMELINE_LABELS, ...input.labels };
  const order = input.byOp?.order;
  const emission =
    order?.issue_date?.trim() || input.op.data_emissao_op?.trim() || null;
  const plannedStart =
    order?.planned_start_date?.trim() || input.op.data_inicio_prevista_op?.trim() || null;
  const plannedEnd =
    order?.due_date?.trim() || input.op.data_fim_prevista_op?.trim() || null;
  const finishReal = order?.finish_date?.trim() || null;
  const orderDelivery = input.orderDeliveryDate?.trim() || null;

  const events: OpTimelineItem[] = [];

  if (emission) {
    events.push({
      id: `emission-${input.op.numero_op}`,
      title: labels.emission,
      occurredAt: emission,
      timeLabel: formatDisplayDate(emission),
      tone: "default",
    });
  }

  if (plannedStart) {
    events.push({
      id: `planned-start-${input.op.numero_op}`,
      title: labels.plannedStart,
      occurredAt: plannedStart,
      timeLabel: formatDisplayDate(plannedStart),
      tone: "info",
    });
  }

  if (orderDelivery) {
    events.push({
      id: `order-delivery-${input.op.numero_op}`,
      title: labels.orderDelivery,
      occurredAt: orderDelivery,
      timeLabel: formatDisplayDate(orderDelivery),
      tone: orderDeliveryTone(orderDelivery),
    });
  }

  if (plannedEnd) {
    events.push({
      id: `planned-end-${input.op.numero_op}`,
      title: labels.plannedEnd,
      occurredAt: plannedEnd,
      timeLabel: formatDisplayDate(plannedEnd),
      tone: plannedEndTone(plannedEnd, orderDelivery),
    });
  }

  const appointments = (input.appointments ?? []).filter((row) =>
    Boolean(row.appointment_date?.trim()),
  );
  if (appointments.length === 1) {
    const row = appointments[0];
    const when = row.appointment_date!.trim();
    events.push({
      id: `appointment-0-${input.op.numero_op}`,
      title: labels.appointment,
      occurredAt: when,
      timeLabel: formatDisplayDate(when),
      detail: row.work_center?.trim() || undefined,
      tone: "info",
    });
  } else if (appointments.length > 1) {
    const sorted = [...appointments].sort((a, b) =>
      sortKey(a.appointment_date).localeCompare(sortKey(b.appointment_date)),
    );
    const first = sorted[0].appointment_date!.trim();
    const last = sorted[sorted.length - 1].appointment_date!.trim();
    events.push({
      id: `appointments-${input.op.numero_op}`,
      title: labels.appointmentsMany(appointments.length),
      occurredAt: first,
      timeLabel:
        first === last
          ? formatDisplayDate(first)
          : `${formatDisplayDate(first)} – ${formatDisplayDate(last)}`,
      tone: "info",
    });
  }

  if (finishReal) {
    events.push({
      id: `finish-${input.op.numero_op}`,
      title: labels.finishReal,
      occurredAt: finishReal,
      timeLabel: formatDisplayDate(finishReal),
      tone: "success",
    });
  }

  return events.sort((a, b) => sortKey(a.occurredAt).localeCompare(sortKey(b.occurredAt)));
}

export type OpHorizontalTimelinePoint = {
  id: string;
  label: string;
  dateIso: string;
  dateLabel: string;
  tone: HorizontalTimelineTone;
  kind: "event" | "today";
  /** Marco atual: último evento ≤ hoje, ou próximo se todos no futuro. */
  isCurrent: boolean;
};

/**
 * Pontos para timeline horizontal, incluindo marcador «Hoje».
 */
export function buildOpHorizontalTimeline(
  events: OpTimelineItem[],
  todayLabel = "Hoje",
): OpHorizontalTimelinePoint[] {
  const todayIso = (() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  })();

  const points: OpHorizontalTimelinePoint[] = events
    .filter((event) => sortKey(event.occurredAt))
    .map((event) => ({
      id: event.id,
      label: String(event.title),
      dateIso: sortKey(event.occurredAt),
      dateLabel: String(event.timeLabel || formatDisplayDate(event.occurredAt)),
      tone: toHorizontalTone(event.tone),
      kind: "event" as const,
      isCurrent: false,
    }));

  points.push({
    id: "today-marker",
    label: todayLabel,
    dateIso: todayIso,
    dateLabel: formatDisplayDate(todayIso),
    tone: "info",
    kind: "today",
    isCurrent: false,
  });

  points.sort((a, b) => {
    const byDate = a.dateIso.localeCompare(b.dateIso);
    if (byDate !== 0) return byDate;
    if (a.kind === "today") return 1;
    if (b.kind === "today") return -1;
    return 0;
  });

  const pastOrTodayEvents = points.filter(
    (point) => point.kind === "event" && point.dateIso <= todayIso,
  );
  const futureEvents = points.filter(
    (point) => point.kind === "event" && point.dateIso > todayIso,
  );
  const currentId =
    pastOrTodayEvents[pastOrTodayEvents.length - 1]?.id ??
    futureEvents[0]?.id ??
    null;

  return points.map((point) => ({
    ...point,
    isCurrent: point.kind === "event" && point.id === currentId,
  }));
}
