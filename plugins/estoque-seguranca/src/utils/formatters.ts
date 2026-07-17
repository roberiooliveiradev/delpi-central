import { ApiClientError, toSectionError } from "../types/api";

export function formatNumberPtBr(value: number, fractionDigits = 2): string {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatCurrencyPtBr(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

/** Preço unitário: até 4 casas (variações pequenas em escala grande). */
export function formatUnitPricePtBr(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

export function formatIntegerPtBr(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

export function formatQuantity(value: number | null | undefined, unit?: string): string {
  if (value === null || value === undefined) return "—";
  const formatted = formatNumberPtBr(value);
  return unit ? `${formatted} ${unit}` : formatted;
}

/** Saldo exibido na tabela: armazéns 01 + 98 + 99. */
export function computeDisplayBalance(item: {
  primary_stock: number;
  warehouse_98_stock: number;
  warehouse_99_stock: number;
}): number {
  return item.primary_stock + item.warehouse_98_stock + item.warehouse_99_stock;
}

/** Déficit exibido: ESTSEG − saldo disponível (01 + 98 + 99), nunca negativo. */
export function computeDisplayDeficit(item: {
  safety_stock: number;
  primary_stock: number;
  warehouse_98_stock: number;
  warehouse_99_stock: number;
}): number {
  const est = item.safety_stock;
  if (est <= 0) return 0;
  return Math.max(est - computeDisplayBalance(item), 0);
}

export function formatApiErrorMessage(error: unknown): string {
  return toSectionError(error).message;
}

export function isPermissionError(error: unknown): boolean {
  if (error instanceof ApiClientError) {
    return error.kind === "auth" || error.kind === "forbidden";
  }
  const message = formatApiErrorMessage(error);
  return /sem permissão|sessão expirada|autenticar novamente|403|401/i.test(message);
}

export { toSectionError };
