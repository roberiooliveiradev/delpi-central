type ProductTypeBadgeProps = {
  productType?: string | null;
};

function normalizeType(productType?: string | null): string {
  const normalized = productType?.trim().toUpperCase();
  if (normalized === "PA" || normalized === "PI") {
    return normalized;
  }
  return productType?.trim() || "—";
}

function typeClass(productType?: string | null): string {
  const normalized = productType?.trim().toUpperCase();
  if (normalized === "PA") return "dp-kpi-badge dp-kpi-badge--info";
  if (normalized === "PI") return "dp-kpi-badge";
  return "dp-kpi-badge";
}

export function ProductTypeBadge({ productType }: ProductTypeBadgeProps) {
  return <span className={typeClass(productType)}>{normalizeType(productType)}</span>;
}
