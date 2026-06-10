export function formatDisplayDate(value: string | null | undefined): string {
  if (!value) return "—";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return value;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

function toIsoDateOnly(value: string): string {
  const match = value.match(/^(\d{4}-\d{2}-\d{2})/);
  return match?.[1] ?? value;
}

export function compareDeliveryDates(
  a: string | null | undefined,
  b: string | null | undefined,
): number {
  if (!a && !b) return 0;
  if (!a) return 1;
  if (!b) return -1;
  return toIsoDateOnly(a).localeCompare(toIsoDateOnly(b));
}

export function getTodayIsoDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Data de entrega já passou e a linha ainda possui saldo pendente. */
export function isDeliveryOverdue(
  dataEntrega: string | null | undefined,
  saldo: number,
): boolean {
  if (!dataEntrega || saldo <= 0) return false;
  return toIsoDateOnly(dataEntrega) < getTodayIsoDate();
}

/** Dias corridos desde a data de entrega até hoje (somente se já venceu). */
export function getDeliveryOverdueDays(
  dataEntrega: string | null | undefined,
): number | null {
  if (!dataEntrega) return null;

  const deliveryIso = toIsoDateOnly(dataEntrega);
  const todayIso = getTodayIsoDate();
  if (deliveryIso >= todayIso) return null;

  const [dy, dm, dd] = deliveryIso.split("-").map(Number);
  const [ty, tm, td] = todayIso.split("-").map(Number);
  const deliveryDate = new Date(dy, dm - 1, dd);
  const todayDate = new Date(ty, tm - 1, td);
  const diffMs = todayDate.getTime() - deliveryDate.getTime();

  return Math.max(1, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
}

export function formatOverdueDaysLabel(days: number): string {
  if (days === 1) return "Atrasado há 1 dia";
  return `Atrasado há ${days} dias`;
}

export function isWithinDateRange(
  value: string | null | undefined,
  start: string,
  end: string,
): boolean {
  if (!value) return false;
  if (start && value < start) return false;
  if (end && value > end) return false;
  return true;
}

export type OpVsPedidoPrazoStatus = "no_prazo" | "atrasado" | "indeterminado";

/** Compara fim previsto da OP com a data de entrega solicitada no pedido. */
export function resolveOpVsPedidoPrazo(
  dataFimPrevistaOp: string | null | undefined,
  dataEntregaPedido: string | null | undefined,
): { status: OpVsPedidoPrazoStatus; label: string } {
  if (!dataFimPrevistaOp || !dataEntregaPedido) {
    return { status: "indeterminado", label: "—" };
  }

  if (compareDeliveryDates(dataFimPrevistaOp, dataEntregaPedido) <= 0) {
    return { status: "no_prazo", label: "No prazo" };
  }

  return { status: "atrasado", label: "Atrasado" };
}
