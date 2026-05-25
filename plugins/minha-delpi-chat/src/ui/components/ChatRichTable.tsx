import { useState, useCallback } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type SortConfig = {
  key: string;
  direction: "asc" | "desc";
} | null;

export function ChatRichTable({
  presentation,
  onDrillDown,
}: {
  presentation: TablePresentation;
  onDrillDown?: (query: string) => void;
}) {
  const { title, columns, rows } = presentation;
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [copied, setCopied] = useState(false);

  const sortedRows = useCallback(() => {
    if (!sortConfig) return rows;

    return [...rows].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;

      const aNum = Number(aVal);
      const bNum = Number(bVal);

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortConfig.direction === "asc" ? aNum - bNum : bNum - aNum;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      const cmp = aStr.localeCompare(bStr, "pt-BR");
      return sortConfig.direction === "asc" ? cmp : -cmp;
    });
  }, [rows, sortConfig]);

  function handleSort(key: string) {
    setSortConfig((prev) => {
      if (prev?.key === key) {
        return prev.direction === "asc"
          ? { key, direction: "desc" }
          : null;
      }
      return { key, direction: "asc" };
    });
  }

  function exportCsv() {
    const BOM = "\uFEFF";
    const header = columns.map((c) => c.label).join(";");
    const body = rows
      .map((row) =>
        columns
          .map((col) => {
            const val = row[col.key];
            if (val == null) return "";
            const str = String(val);
            return str.includes(";") || str.includes('"')
              ? `"${str.replace(/"/g, '""')}"`
              : str;
          })
          .join(";"),
      )
      .join("\n");

    const csv = BOM + header + "\n" + body;
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title || "dados"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function copyToClipboard() {
    const header = columns.map((c) => c.label).join("\t");
    const body = rows
      .map((row) =>
        columns.map((col) => String(row[col.key] ?? "")).join("\t"),
      )
      .join("\n");

    navigator.clipboard.writeText(header + "\n" + body).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const sorted = sortedRows();

  return (
    <div className="mdc-rich-table">
      <div className="mdc-rich-table__header">
        <span className="mdc-rich-table__title">{title}</span>
        <div className="mdc-rich-table__actions">
          <button
            className="mdc-rich-table__btn"
            onClick={copyToClipboard}
            title="Copiar tabela"
          >
            {copied ? "✓ Copiado" : "Copiar"}
          </button>
          <button
            className="mdc-rich-table__btn"
            onClick={exportCsv}
            title="Baixar CSV"
          >
            ↓ CSV
          </button>
        </div>
      </div>

      <div className="mdc-rich-table__scroll">
        <table className="mdc-rich-table__table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={
                    sortConfig?.key === col.key
                      ? `mdc-rich-table__th--sorted-${sortConfig.direction}`
                      : ""
                  }
                >
                  {col.label}
                  {sortConfig?.key === col.key && (
                    <span className="mdc-rich-table__sort-icon">
                      {sortConfig.direction === "asc" ? " ▲" : " ▼"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => (
              <tr
                key={idx}
                className={onDrillDown ? "mdc-rich-table__tr--clickable" : ""}
                onClick={() => {
                  if (!onDrillDown) return;
                  const query = buildDrillDownQuery(row, columns);
                  if (query) onDrillDown(query);
                }}
                title={onDrillDown ? "Clique para detalhar" : undefined}
              >
                {columns.map((col) => (
                  <td key={col.key} className={getAlignClass(col.key, row[col.key], col.dataType)}>
                    {formatCellValue(row[col.key], col.key, col.dataType)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length > 0 && (
        <div className="mdc-rich-table__footer">
          {rows.length} registro(s)
        </div>
      )}
    </div>
  );
}

function buildDrillDownQuery(
  row: Record<string, unknown>,
  columns: { key: string; label: string }[],
): string | null {
  const codeCol = columns.find((c) =>
    /^(code|codigo|cod|id|numero|number|nropor)$/i.test(c.key)
  );
  const descCol = columns.find((c) =>
    /^(description|descricao|descri|nome|name|produto|product)$/i.test(c.key)
  );

  const code = codeCol ? String(row[codeCol.key] ?? "") : "";
  const desc = descCol ? String(row[descCol.key] ?? "") : "";

  if (code) {
    return `Detalhe do item ${code}${desc ? ` (${desc})` : ""}`;
  }
  if (desc) {
    return `Mais informações sobre ${desc}`;
  }
  const firstVal = String(row[columns[0]?.key] ?? "");
  return firstVal ? `Detalhe de ${firstVal}` : null;
}

const CURRENCY_KEYS = /valor|preco|price|custo|cost|total|revenue|faturamento|receita|saldo|vlr|vl_/i;
const PERCENT_KEYS = /pct|percent|taxa|rate|margem|margin|otd|giro|eficiencia/i;
const DATE_KEYS = /data|date|emissao|criacao|atualizacao|inicio|fim|vencimento|dt_|created|updated/i;
const QTY_KEYS = /qtd|quantidade|qty|quantity|saldo|disponivel|reservado|estoque|volume/i;

type ColumnType = "text" | "number" | "currency" | "date" | "percent" | "quantity" | undefined;

function inferColumnType(key: string, dataType?: ColumnType): ColumnType {
  if (dataType) return dataType;
  if (CURRENCY_KEYS.test(key)) return "currency";
  if (PERCENT_KEYS.test(key)) return "percent";
  if (DATE_KEYS.test(key)) return "date";
  if (QTY_KEYS.test(key)) return "quantity";
  return undefined;
}

function getAlignClass(key: string, value: unknown, dataType?: ColumnType): string {
  const t = inferColumnType(key, dataType);
  if (typeof value === "number" || t === "currency" || t === "quantity" || t === "percent" || t === "number") {
    return "mdc-rich-table__td--right";
  }
  return "";
}

function formatCellValue(value: unknown, columnKey?: string, dataType?: ColumnType): string {
  if (value == null) return "—";
  if (typeof value === "boolean") return value ? "Sim" : "Não";

  const key = columnKey || "";
  const colType = inferColumnType(key, dataType);

  if (typeof value === "number") {
    if (colType === "currency") {
      return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    }
    if (colType === "percent") {
      return `${value.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 })}%`;
    }
    if (colType === "quantity") {
      return value.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    }
    if (Number.isInteger(value)) return value.toLocaleString("pt-BR");
    return value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  }

  const str = String(value);

  if (colType === "date" || /^\d{4}-\d{2}-\d{2}/.test(str)) {
    const d = new Date(str);
    if (!isNaN(d.getTime())) {
      if (str.includes("T") || str.length > 10) {
        return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
      }
      return d.toLocaleDateString("pt-BR");
    }
  }

  return str;
}
