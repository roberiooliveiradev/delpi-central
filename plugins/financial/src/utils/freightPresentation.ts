import { copy } from "../content/copy";
import type { FreightAllocation, FreightInvoice, FreightSituation } from "../types";
import { EMPTY_VALUE, formatCurrency, formatPercent } from "./formatNumbers";

/**
 * O BFF envia decimais como string para não perder centavos no JSON. A tela
 * converte só na hora de formatar — nenhum cálculo de rateio acontece aqui.
 */
export function decimalToNumber(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatDecimalCurrency(value: string | null | undefined): string {
  return formatCurrency(decimalToNumber(value));
}

/** Duas casas: é a precisão com que o BFF compara o percentual com o limite. */
export function formatFreightPercent(value: string | null | undefined): string {
  return formatPercent(decimalToNumber(value), 2);
}

/** Filial sem limite não é «0%» — é ausência de regra, e precisa aparecer assim. */
export function formatFreightLimit(value: string | null | undefined): string {
  const parsed = decimalToNumber(value);
  return parsed === null ? copy.freight.noLimitBadge : formatPercent(parsed, 2);
}

export type FreightSituationTone = "success" | "danger" | "warning";

export function freightSituationTone(situation: FreightSituation): FreightSituationTone {
  if (situation === "above_limit") return "danger";
  if (situation === "inconsistent") return "warning";
  return "success";
}

export function freightSituationLabel(situation: FreightSituation): string {
  return copy.freight.situations[situation];
}

/**
 * Tom da linha na tabela do kit: acima do limite e inconsistente pedem
 * destaques distintos. O visual mora no `plugin-ui`; aqui só a semântica.
 */
export function freightRowClassName(situation: FreightSituation): string | undefined {
  if (situation === "above_limit") return "delpi-ui-table__row--tone-danger";
  if (situation === "inconsistent") return "delpi-ui-table__row--tone-warning";
  return undefined;
}

/**
 * A base de rateio soma todas as NFs do CT-e, inclusive as fora do filtro. Se
 * ela é maior que a mercadoria desta nota, o valor bruto do CT-e está dividido
 * com notas que a tela não mostra — o usuário precisa saber antes de conferir.
 */
export function hasPartialBase(invoice: FreightInvoice, allocation: FreightAllocation): boolean {
  if (allocation.linkedInvoiceCount > 1) return true;
  const base = decimalToNumber(allocation.allocationBase);
  const goods = decimalToNumber(invoice.goodsValue);
  return base !== null && goods !== null && base > goods;
}

export function freightReasonLabels(
  reasonCodes: string[],
  reasonsByCode: Map<string, string>,
): string {
  if (!reasonCodes.length) return EMPTY_VALUE;
  return reasonCodes.map((code) => reasonsByCode.get(code) ?? code).join(" · ");
}
