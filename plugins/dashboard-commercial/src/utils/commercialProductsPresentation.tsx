import type { DataTableColumn } from "../components/table";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { CommercialProduct } from "../types/commercial";

const PRODUCT_TYPE_LABELS: Record<string, string> = {
  PA: "Acabado",
  PI: "Intermediário",
  MP: "Matéria-prima",
  ME: "Mercadoria",
  BN: "Beneficiamento",
  AI: "Ativo imobilizado",
};

function parseProductDescription(description?: string | null): {
  title: string;
  reference?: string;
} {
  const trimmed = description?.trim() ?? "";
  if (!trimmed) return { title: "—" };

  const match = trimmed.match(/^(.*)\s+\(([^)]+)\)\s*$/);
  if (!match) return { title: trimmed };

  const title = match[1].trim();
  const reference = match[2].trim();
  if (!title) return { title: trimmed };

  return { title, reference: reference || undefined };
}

export function parseProductTitle(description?: string | null): string {
  return parseProductDescription(description).title;
}

function renderProductType(type?: string | null) {
  const normalized = type?.trim().toUpperCase();
  if (!normalized) return "—";

  const label = PRODUCT_TYPE_LABELS[normalized] ?? normalized;
  const badgeClass =
    normalized === "PI"
      ? "dc-product-type-badge dc-product-type-badge--pi"
      : normalized === "PA"
        ? "dc-product-type-badge dc-product-type-badge--pa"
        : "dc-product-type-badge";

  return (
    <span className={badgeClass} title={`Tipo ${normalized}`}>
      {label}
    </span>
  );
}

function renderProductDescription(description?: string | null) {
  const { title, reference } = parseProductDescription(description);

  return (
    <div className="dc-product-description">
      <span className="dc-product-description__title">{title}</span>
      {reference ? (
        <span className="dc-product-description__ref">Referência {reference}</span>
      ) : null}
    </div>
  );
}

function renderProductQuantity(value?: number | null) {
  const quantity = value ?? 0;
  const className =
    quantity > 0
      ? "dc-product-qtd dc-product-qtd--active"
      : "dc-product-qtd";

  return <span className={className}>{quantity.toLocaleString("pt-BR")}</span>;
}

export const commercialProductColumns: DataTableColumn<CommercialProduct>[] = [
  {
    key: "code",
    header: "Código",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.productCode,
    render: (row) => row.code || "—",
  },
  {
    key: "description",
    header: "Descrição",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.productDescription,
    className: "dc-table__col--wide",
    render: (row) => renderProductDescription(row.description),
  },
  {
    key: "group",
    header: "Grupo",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.productGroup,
    render: (row) => row.group_code || "—",
  },
  {
    key: "type",
    header: "Tipo",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.productType,
    render: (row) => renderProductType(row.type),
  },
  {
    key: "qtd_pi",
    header: "Qtd PI",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.productQtdPi,
    render: (row) => renderProductQuantity(row.qtd_pi),
  },
];
