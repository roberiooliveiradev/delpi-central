import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import {
  formatOverdueDaysLabel,
  getDeliveryOverdueDays,
  isDeliveryOverdue,
} from "./dates";
import { getAllocatedStock } from "./stockAllocation";

export type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

export type LineStatusKind =
  | "atrasado_sem_estoque"
  | "atrasado_com_estoque"
  | "atrasado_parcial"
  | "pode_faturar"
  | "sem_estoque"
  | "estoque_parcial";

export type StatusBadgeDescriptor = {
  kind: LineStatusKind;
  label: string;
  tone: BadgeTone;
};

function hasFullAllocatedStock(item: PedidosVendaAbertosItem, estoque: number): boolean {
  return item.saldo > 0 && estoque >= item.saldo;
}

function hasPartialAllocatedStock(item: PedidosVendaAbertosItem, estoque: number): boolean {
  return estoque > 0 && estoque < item.saldo;
}

function hasNoAllocatedStock(estoque: number): boolean {
  return estoque <= 0;
}

export function getLineStatus(item: PedidosVendaAbertosItem): StatusBadgeDescriptor {
  const estoque = getAllocatedStock(item);
  const overdue = isDeliveryOverdue(item.data_entrega, item.saldo);

  if (overdue) {
    if (hasNoAllocatedStock(estoque)) {
      const days = getDeliveryOverdueDays(item.data_entrega) ?? 1;
      return {
        kind: "atrasado_sem_estoque",
        label: formatOverdueDaysLabel(days),
        tone: "danger",
      };
    }
    if (hasFullAllocatedStock(item, estoque)) {
      return {
        kind: "atrasado_com_estoque",
        label: "Pedido atrasado com saldo em estoque",
        tone: "warning",
      };
    }
    return {
      kind: "atrasado_parcial",
      label: "Atrasado com estoque parcial",
      tone: "warning",
    };
  }

  if (hasFullAllocatedStock(item, estoque)) {
    return {
      kind: "pode_faturar",
      label: "Pode faturar",
      tone: "success",
    };
  }
  if (hasNoAllocatedStock(estoque)) {
    return {
      kind: "sem_estoque",
      label: "Sem estoque",
      tone: "danger",
    };
  }
  if (hasPartialAllocatedStock(item, estoque)) {
    return {
      kind: "estoque_parcial",
      label: "Estoque parcial",
      tone: "warning",
    };
  }

  return {
    kind: "sem_estoque",
    label: "Sem estoque",
    tone: "danger",
  };
}

export type StockFilter = "" | "com_estoque" | "parcial" | "sem_estoque";

const FATURAVEL_KINDS: LineStatusKind[] = ["pode_faturar", "atrasado_com_estoque"];
const PARCIAL_KINDS: LineStatusKind[] = ["estoque_parcial", "atrasado_parcial"];
const SEM_ESTOQUE_KINDS: LineStatusKind[] = ["sem_estoque", "atrasado_sem_estoque"];

export function matchesStockFilter(item: PedidosVendaAbertosItem, filter: StockFilter): boolean {
  if (!filter) return true;

  const kind = getLineStatus(item).kind;
  if (filter === "com_estoque") return FATURAVEL_KINDS.includes(kind);
  if (filter === "parcial") return PARCIAL_KINDS.includes(kind);
  if (filter === "sem_estoque") return SEM_ESTOQUE_KINDS.includes(kind);
  return true;
}

export function isFaturavelStatus(kind: LineStatusKind): boolean {
  return FATURAVEL_KINDS.includes(kind);
}

export function isParcialStatus(kind: LineStatusKind): boolean {
  return PARCIAL_KINDS.includes(kind);
}
