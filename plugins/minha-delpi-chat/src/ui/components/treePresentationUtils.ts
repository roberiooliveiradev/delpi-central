import type { ChatPresentation, ChatTreeNode } from "../../data/api/chatTypes";

export type TreeFlatRow = {
  nivel: number;
  codigo: string;
  descricao: string;
  tipo: string;
  unidade: string;
  quantidade: string;
  caminho: string;
};

export type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;

const TREE_COLUMNS = [
  { key: "nivel", label: "Nível" },
  { key: "codigo", label: "Código" },
  { key: "descricao", label: "Descrição" },
  { key: "tipo", label: "Tipo" },
  { key: "unidade", label: "Unid." },
  { key: "quantidade", label: "Qtde" },
  { key: "caminho", label: "Caminho" },
] as const;

function formatQuantity(value: string | number | undefined): string {
  if (value === undefined || value === null || value === "") {
    return "";
  }

  const numeric = Number(value);

  if (!Number.isNaN(numeric)) {
    return numeric.toLocaleString("pt-BR", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 4,
    });
  }

  return String(value);
}

export function flattenTreeToRows(
  root: ChatTreeNode,
  depth = 0,
  path: string[] = [],
): TreeFlatRow[] {
  const currentPath = [...path, root.label || root.id];
  const rows: TreeFlatRow[] = [
    {
      nivel: depth,
      codigo: root.label || root.id,
      descricao: root.subtitle || "",
      tipo: root.badge || "",
      unidade: String(root.meta?.unit ?? ""),
      quantidade: formatQuantity(root.meta?.quantity),
      caminho: currentPath.join(" > "),
    },
  ];

  for (const child of root.children ?? []) {
    rows.push(...flattenTreeToRows(child, depth + 1, currentPath));
  }

  return rows;
}

export function treePresentationToTable(presentation: TreePresentation) {
  const rows = flattenTreeToRows(presentation.root).map((row) => ({ ...row }));

  return {
    type: "table" as const,
    title: presentation.title,
    columns: TREE_COLUMNS.map((column) => ({
      key: column.key,
      label: column.label,
      dataType: column.key === "quantidade" ? ("quantity" as const) : undefined,
    })),
    rows,
  };
}

export function treePresentationToClipboardText(presentation: TreePresentation): string {
  const rows = flattenTreeToRows(presentation.root);
  const header = TREE_COLUMNS.map((column) => column.label).join("\t");
  const body = rows
    .map((row) =>
      TREE_COLUMNS.map((column) => String(row[column.key as keyof TreeFlatRow] ?? "")).join("\t"),
    )
    .join("\n");

  return `${presentation.title}\n${header}\n${body}`;
}

export function exportTreeToCsv(presentation: TreePresentation) {
  const rows = flattenTreeToRows(presentation.root);
  const BOM = "\uFEFF";
  const header = TREE_COLUMNS.map((column) => column.label).join(";");
  const body = rows
    .map((row) =>
      TREE_COLUMNS.map((column) => {
        const value = String(row[column.key as keyof TreeFlatRow] ?? "");
        return value.includes(";") || value.includes('"')
          ? `"${value.replace(/"/g, '""')}"`
          : value;
      }).join(";"),
    )
    .join("\n");

  const csv = BOM + header + "\n" + body;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${sanitizeFilename(presentation.title || "arvore")}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function sanitizeFilename(value: string): string {
  return value.replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_").slice(0, 80) || "dados";
}
