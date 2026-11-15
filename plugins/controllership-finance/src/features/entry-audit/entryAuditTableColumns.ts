import type { ReactNode } from "react";

import type { EntryAuditDocument, EntryAuditTes } from "../../api/entryAuditApi";
import type { DataTableColumn } from "../../app/cfDataTableUi";
import type { EntryAuditOption } from "../../api/entryAuditApi";
import {
  displayValue,
  formatBranchLabel,
  formatMoneyBRL,
  formatNoteSeries,
  type EntryAuditTab,
} from "./entryAuditPresentation";

type DocRow = EntryAuditDocument | EntryAuditTes;

function formatIsoDate(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  const raw = String(value).slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [year, month, day] = raw.split("-");
    return `${day}/${month}/${year}`;
  }
  return displayValue(value);
}

function formatAmount(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return formatMoneyBRL(value);
  }
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? formatMoneyBRL(parsed) : displayValue(value);
  }
  return displayValue(value);
}

function sortableColumn(
  key: string,
  header: string,
  render: (row: DocRow) => ReactNode,
  sortWhitelist: ReadonlySet<string>,
  align?: "left" | "right",
): DataTableColumn<DocRow> {
  return {
    key,
    header,
    sortable: sortWhitelist.has(key),
    render,
    align,
  };
}

const DOCUMENT_SORT = new Set([
  "document_number",
  "received_date",
  "issue_date",
  "supplier_name",
  "amount",
  "situation",
  "series",
  "branch",
  "access_key",
]);

const UNMATCHED_SORT = new Set([
  "document_number",
  "supplier_name",
  "situation",
  "series",
  "branch",
  "nature",
  "received_date",
  "amount",
  "access_key",
]);

const CTE_SORT = new Set([
  "document_number",
  "branch",
  "access_key",
  "series",
  "supplier_name",
  "amount",
  "received_date",
]);

const TES_SORT = new Set(["tes_code", "items", "description", "branch"]);

function baseDocumentColumns(
  sortWhitelist: ReadonlySet<string>,
  branchOptions: EntryAuditOption[],
  options?: { situation?: boolean; nature?: boolean },
): DataTableColumn<DocRow>[] {
  const cols: DataTableColumn<DocRow>[] = [
    sortableColumn(
      "branch",
      "Filial",
      (row) => formatBranchLabel(String(row.branch ?? ""), branchOptions),
      sortWhitelist,
    ),
    sortableColumn(
      "document_number",
      "Nota/Série",
      (row) =>
        formatNoteSeries(
          "document_number" in row ? row.document_number : undefined,
          "series" in row ? (row as EntryAuditDocument).series : undefined,
        ),
      sortWhitelist,
    ),
    sortableColumn(
      "supplier_name",
      "Fornecedor",
      (row) => displayValue("supplier_name" in row ? row.supplier_name : undefined),
      sortWhitelist,
    ),
    sortableColumn(
      "issue_date",
      "Emissão",
      (row) => formatIsoDate("issue_date" in row ? row.issue_date : undefined),
      sortWhitelist,
    ),
    sortableColumn(
      "received_date",
      "Recebimento",
      (row) =>
        formatIsoDate("received_date" in row ? row.received_date : undefined),
      sortWhitelist,
    ),
    sortableColumn(
      "amount",
      "Valor",
      (row) => {
        const raw =
          "amount" in row
            ? row.amount
            : "comparison" in row && row.comparison
              ? (row.comparison as { gross?: unknown }).gross
              : undefined;
        return formatAmount(raw);
      },
      sortWhitelist,
      "right",
    ),
  ];
  if (options?.situation !== false) {
    cols.push(
      sortableColumn(
        "situation",
        "Situação",
        (row) => displayValue("situation" in row ? row.situation : undefined),
        sortWhitelist,
      ),
    );
  }
  if (options?.nature) {
    cols.push(
      sortableColumn(
        "nature",
        "Natureza",
        (row) => displayValue("nature" in row ? (row as EntryAuditDocument).nature : undefined),
        sortWhitelist,
      ),
    );
  }
  cols.push(
    sortableColumn(
      "access_key",
      "Chave de acesso",
      (row) => displayValue("access_key" in row ? row.access_key : undefined),
      sortWhitelist,
    ),
  );
  return cols;
}

function tesColumns(branchOptions: EntryAuditOption[]): DataTableColumn<DocRow>[] {
  return [
    sortableColumn(
      "branch",
      "Filial",
      (row) => formatBranchLabel(String(row.branch ?? ""), branchOptions),
      TES_SORT,
    ),
    sortableColumn(
      "tes_code",
      "TES",
      (row) =>
        displayValue(
          ("tes_code" in row && row.tes_code) ||
            row.tes ||
            row.code,
        ),
      TES_SORT,
    ),
    sortableColumn(
      "description",
      "Descrição",
      (row) => displayValue(row.description),
      TES_SORT,
    ),
    sortableColumn(
      "items",
      "Itens",
      (row) => {
        const items =
          ("sf4" in row &&
            row.sf4 &&
            (row.sf4 as { items?: number }).items) ??
          ("items" in row ? row.items : undefined);
        return displayValue(items ?? "");
      },
      TES_SORT,
      "right",
    ),
  ];
}

/** Colunas das abas de documentos / sem par / CT-e / TES / lançadas fora. */
export function buildEntryAuditGenericColumns(
  tab: EntryAuditTab,
  branchOptions: EntryAuditOption[],
): DataTableColumn<DocRow>[] {
  if (tab === "tes") return tesColumns(branchOptions);
  if (tab === "cte") {
    return baseDocumentColumns(CTE_SORT, branchOptions, { situation: false });
  }
  if (tab === "unmatched") {
    return baseDocumentColumns(UNMATCHED_SORT, branchOptions, { nature: true });
  }
  return baseDocumentColumns(DOCUMENT_SORT, branchOptions);
}