import type { PortfolioBillingAmountNature } from "../../../content/billingNature";
import type { CommercialRolByProductItem } from "../../../types/analytics";

export type PortfolioBillingByProductRow = {
  id: string;
  label: string;
  domestic: number;
  export: number;
  total: number;
  sharePct: number | null;
  isTotal?: boolean;
};

export function amountFromRolItem(
  item: CommercialRolByProductItem,
  nature: PortfolioBillingAmountNature,
  market: "domestic" | "export" | "all",
): { domestic: number; export: number; total: number } {
  const domestic =
    nature === "gross"
      ? Number(item.domestic_gross_revenue ?? 0)
      : Number(item.domestic_rol ?? 0);
  const exportValue =
    nature === "gross"
      ? Number(item.export_gross_revenue ?? 0)
      : Number(item.export_rol ?? 0);
  const total =
    nature === "gross"
      ? Number(item.gross_revenue ?? domestic + exportValue)
      : Number(item.rol ?? domestic + exportValue);
  if (market === "domestic") {
    return { domestic, export: 0, total: domestic };
  }
  if (market === "export") {
    return { domestic: 0, export: exportValue, total: exportValue };
  }
  return { domestic, export: exportValue, total };
}

export function mapRolByProductRows(
  items: CommercialRolByProductItem[],
  options: {
    nature: PortfolioBillingAmountNature;
    market: "domestic" | "export" | "all";
    groupBy: "product" | "product_group";
  },
): PortfolioBillingByProductRow[] {
  const { nature, market, groupBy } = options;
  const rows: PortfolioBillingByProductRow[] = items.map((item, index) => {
    const amounts = amountFromRolItem(item, nature, market);
    const label =
      groupBy === "product_group"
        ? `${item.product_group || "—"} · ${item.product_name || item.product_group || "—"}`
        : `${item.product_code || "—"} · ${item.product_name || item.product_code || "—"}`;
    return {
      id: `${item.product_code || item.product_group || index}`,
      label,
      domestic: amounts.domestic,
      export: amounts.export,
      total: amounts.total,
      sharePct: item.share_pct ?? null,
    };
  });
  if (!rows.length) return rows;
  const sumDomestic = rows.reduce((acc, row) => acc + row.domestic, 0);
  const sumExport = rows.reduce((acc, row) => acc + row.export, 0);
  const sumTotal = rows.reduce((acc, row) => acc + row.total, 0);
  rows.push({
    id: "__total__",
    label: "Total",
    domestic: sumDomestic,
    export: sumExport,
    total: sumTotal,
    sharePct: sumTotal > 0 ? 100 : null,
    isTotal: true,
  });
  return rows;
}

export function formatSharePct(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} %`;
}

export function formatCnpj(raw: string | null | undefined): string {
  const digits = String(raw || "").replace(/\D/g, "");
  if (digits.length === 14) {
    return digits.replace(
      /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
      "$1.$2.$3/$4-$5",
    );
  }
  if (digits.length === 11) {
    return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
  }
  return raw?.trim() || "—";
}

export function formatCityState(
  city: string | null | undefined,
  state: string | null | undefined,
): string {
  const cityLabel = (city || "").trim();
  const stateLabel = (state || "").trim();
  if (cityLabel && stateLabel) return `${cityLabel}/${stateLabel}`;
  return cityLabel || stateLabel || "—";
}
