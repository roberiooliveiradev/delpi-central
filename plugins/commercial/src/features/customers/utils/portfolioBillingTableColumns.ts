import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";

export type PortfolioBillingColumnItem = {
  key: string;
  label: string;
};

export const PORTFOLIO_BY_PRODUCT_COLUMN_CATALOG: readonly PortfolioBillingColumnItem[] = [
  { key: "label", label: CUSTOMER_BILLING_CONTENT.colProduct },
  { key: "domestic", label: CUSTOMER_BILLING_CONTENT.colDomestic },
  { key: "export", label: CUSTOMER_BILLING_CONTENT.colExport },
  { key: "total", label: CUSTOMER_BILLING_CONTENT.colTotal },
  { key: "share", label: CUSTOMER_BILLING_CONTENT.colShare },
] as const;

export const PORTFOLIO_ABC_COLUMN_CATALOG: readonly PortfolioBillingColumnItem[] = [
  { key: "customer", label: CUSTOMER_BILLING_CONTENT.colCustomer },
  { key: "cnpj", label: CUSTOMER_BILLING_CONTENT.colCnpj },
  { key: "city", label: CUSTOMER_BILLING_CONTENT.colCityState },
  { key: "share", label: CUSTOMER_BILLING_CONTENT.colShare },
] as const;

export const PORTFOLIO_RANKING_COLUMN_CATALOG: readonly PortfolioBillingColumnItem[] = [
  { key: "rank", label: "#" },
  { key: "customer", label: "Cliente" },
  { key: "seller", label: "Vendedor" },
  { key: "trend", label: "Tendência" },
  { key: "current", label: "Faturamento atual" },
  { key: "prior", label: "Faturamento ano ant." },
  { key: "deltaPct", label: "Delta %" },
] as const;

export const PORTFOLIO_BY_PRODUCT_COLUMNS_STORAGE_KEY =
  "commercial:portfolio-billing-by-product:table-columns:v1";
export const PORTFOLIO_BY_PRODUCT_FONT_STORAGE_KEY =
  "commercial:portfolio-billing-by-product:table-font-size:v1";

export const PORTFOLIO_ABC_COLUMNS_STORAGE_KEY =
  "commercial:portfolio-billing-abc:table-columns:v1";
export const PORTFOLIO_ABC_FONT_STORAGE_KEY =
  "commercial:portfolio-billing-abc:table-font-size:v1";

export const PORTFOLIO_RANKING_COLUMNS_STORAGE_KEY =
  "commercial:portfolio-billing-ranking:table-columns:v1";
export const PORTFOLIO_RANKING_FONT_STORAGE_KEY =
  "commercial:portfolio-billing-ranking:table-font-size:v1";
