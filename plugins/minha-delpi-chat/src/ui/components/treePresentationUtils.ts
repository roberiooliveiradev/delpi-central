import type { ChatPresentation, ChatTreeNode } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";

export type TreeFlatRow = {
  nivel: number;
  codigo: string;
  descricao: string;
  tipo: string;
  unidade: string;
  quantidade: string;
};

export type TreeBlockSection = {
  heading: string;
  nivel: number;
  rows: TreeFlatRow[];
};

export type TreePresentation = Extract<ChatPresentation, { type: "tree" }>;

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type BlockChildColumn = {
  key: keyof TreeFlatRow;
  label: string;
  dataType?: "text" | "number" | "currency" | "date" | "percent" | "quantity";
};

const BLOCK_CHILD_COLUMNS: readonly BlockChildColumn[] = [
  { key: "nivel", label: "Nível" },
  { key: "codigo", label: "Código" },
  { key: "descricao", label: "Descrição" },
  { key: "tipo", label: "Tipo" },
  { key: "unidade", label: "Unid." },
  { key: "quantidade", label: "Qtde", dataType: "quantity" },
];

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

/** Meta de nó de árvore — BOM (`quantity`/`unit`) e estoque (`available_quantity`, etc.). */
export function formatTreeNodeMeta(meta?: Record<string, string | number>): string {
  if (!meta) {
    return "";
  }

  const unit = String(meta.unit ?? "un.").trim();
  const hasStockDetail =
    meta.available_quantity !== undefined ||
    meta.current_quantity !== undefined ||
    meta.committed_quantity !== undefined;

  if (hasStockDetail) {
    const parts: string[] = [];
    const available = meta.available_quantity ?? meta.quantity;

    if (available !== undefined && available !== null && available !== "") {
      parts.push(`Disponível: ${formatQuantity(available)}`);
    }

    if (meta.current_quantity !== undefined && meta.current_quantity !== null && meta.current_quantity !== "") {
      parts.push(`Saldo atual: ${formatQuantity(meta.current_quantity)}`);
    }

    if (
      meta.committed_quantity !== undefined &&
      meta.committed_quantity !== null &&
      meta.committed_quantity !== ""
    ) {
      parts.push(`Empenhado: ${formatQuantity(meta.committed_quantity)}`);
    }

    if (parts.length) {
      return `${parts.join(" · ")}${unit ? ` ${unit}` : ""}`.trim();
    }
  }

  if (meta.quantity !== undefined && meta.quantity !== null && meta.quantity !== "") {
    const formatted = formatQuantity(meta.quantity);

    return unit ? `${formatted} ${unit}` : `Qtd: ${formatted}`;
  }

  return "";
}

function treeNodeToChildRow(node: ChatTreeNode, depth: number): TreeFlatRow {
  return {
    nivel: depth,
    codigo: node.label || node.id,
    descricao: node.subtitle || "",
    tipo: node.badge || "",
    unidade: String(node.meta?.unit ?? "un."),
    quantidade: formatQuantity(node.meta?.available_quantity ?? node.meta?.quantity),
  };
}

export function formatTreeBlockHeading(node: ChatTreeNode, depth: number): string {
  const code = String(node.label || node.id || "").trim();
  const description = String(node.subtitle || "").trim();
  const badge = String(node.badge || "").trim();
  const quantity = formatQuantity(node.meta?.available_quantity ?? node.meta?.quantity);
  const unit = String(node.meta?.unit ?? "").trim();
  const label = description ? `${code} — ${description}` : code;
  const metaParts = [
    badge,
    quantity && unit ? `${quantity} ${unit}` : quantity || unit,
  ].filter(Boolean);

  const meta = metaParts.length ? ` (${metaParts.join(" · ")})` : "";

  return `${label}${meta}`.trim() || `Nível ${depth}`;
}

export function collectTreeBlockSections(
  node: ChatTreeNode,
  depth = 0,
): TreeBlockSection[] {
  const children = node.children ?? [];
  const sections: TreeBlockSection[] = [];

  if (children.length > 0) {
    sections.push({
      heading: formatTreeBlockHeading(node, depth),
      nivel: depth,
      rows: children.map((child) => treeNodeToChildRow(child, depth + 1)),
    });

    for (const child of children) {
      sections.push(...collectTreeBlockSections(child, depth + 1));
    }
  }

  return sections;
}

function blockRowsToTableRows(rows: TreeFlatRow[]): Record<string, unknown>[] {
  return rows.map((row) => ({ ...row }));
}

export function treePresentationToBlockTables(presentation: TreePresentation): TablePresentation[] {
  const blocks = collectTreeBlockSections(presentation.root);

  return blocks.map((block) => ({
    type: "table" as const,
    title: block.heading,
    columns: BLOCK_CHILD_COLUMNS.map((column) => ({
      key: column.key,
      label: column.label,
      dataType: column.dataType,
    })),
    rows: blockRowsToTableRows(block.rows),
  }));
}

export function treePresentationToTable(presentation: TreePresentation): TablePresentation {
  const blocks = treePresentationToBlockTables(presentation);

  if (!blocks.length) {
    return {
      type: "table",
      title: presentation.title,
      columns: BLOCK_CHILD_COLUMNS.map((column) => ({
        key: column.key,
        label: column.label,
        dataType: column.dataType,
      })),
      rows: [],
    };
  }

  if (blocks.length === 1) {
    return {
      ...blocks[0],
      title: presentation.title,
    };
  }

  return {
    type: "table",
    title: presentation.title,
    columns: blocks[0].columns,
    rows: blocks.flatMap((block, index) => {
      const separator =
        index === 0
          ? []
          : [
              {
                nivel: "",
                codigo: "",
                descricao: `— ${block.title} —`,
                tipo: "",
                unidade: "",
                quantidade: "",
              },
            ];

      return [...separator, ...block.rows];
    }),
  };
}

export function expandTreeSegmentsToBlockTables(
  segments: AssistantContentSegment[],
): AssistantContentSegment[] {
  return segments.flatMap((segment) => {
    if (segment.kind !== "tree") {
      return [segment];
    }

    const blocks = treePresentationToBlockTables(segment.presentation);

    if (!blocks.length) {
      return [
        {
          kind: "table" as const,
          presentation: treePresentationToTable(segment.presentation),
        },
      ];
    }

    return blocks.map((presentation) => ({
      kind: "table" as const,
      presentation,
    }));
  });
}

export function treePresentationToClipboardText(presentation: TreePresentation): string {
  const blocks = collectTreeBlockSections(presentation.root);
  const header = BLOCK_CHILD_COLUMNS.map((column) => column.label).join("\t");
  const sections = blocks.map((block) => {
    const body = block.rows
      .map((row) =>
        BLOCK_CHILD_COLUMNS.map((column) =>
          String(row[column.key as keyof TreeFlatRow] ?? ""),
        ).join("\t"),
      )
      .join("\n");

    return `${block.heading}\n${header}\n${body}`;
  });

  return [presentation.title, ...sections].filter(Boolean).join("\n\n");
}

export function exportTreeToCsv(presentation: TreePresentation) {
  const blocks = collectTreeBlockSections(presentation.root);
  const BOM = "\uFEFF";
  const header = BLOCK_CHILD_COLUMNS.map((column) => column.label).join(";");
  const sections = blocks.map((block) => {
    const body = block.rows
      .map((row) =>
        BLOCK_CHILD_COLUMNS.map((column) => {
          const value = String(row[column.key as keyof TreeFlatRow] ?? "");
          return value.includes(";") || value.includes('"')
            ? `"${value.replace(/"/g, '""')}"`
            : value;
        }).join(";"),
      )
      .join("\n");

    return `${block.heading}\n${header}\n${body}`;
  });

  const csv = BOM + sections.join("\n\n");
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

/** @deprecated Mantido para testes legados; prefira collectTreeBlockSections. */
export function flattenTreeToRows(
  root: ChatTreeNode,
  depth = 0,
): TreeFlatRow[] {
  const rows: TreeFlatRow[] = [treeNodeToChildRow(root, depth)];

  for (const child of root.children ?? []) {
    rows.push(...flattenTreeToRows(child, depth + 1));
  }

  return rows;
}
