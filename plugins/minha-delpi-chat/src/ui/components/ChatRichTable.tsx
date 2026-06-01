import { useState, useCallback } from "react";
import type { ChatPresentation } from "../../data/api/chatTypes";
import { ExpandButton } from "./ChatExpandModal";
import { buildTableRowMenuActions } from "./chatDrillDown";
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import { formatCellValue, getAlignClass } from "./tableCellFormatting";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

type SortConfig = {
  key: string;
  direction: "asc" | "desc";
} | null;

export function ChatRichTable({
  presentation,
  hideTitle = false,
  hideToolbar = false,
  onDrillDown,
}: {
  presentation: TablePresentation;
  hideTitle?: boolean;
  /** Oculta cabeçalho com ações (ex.: dentro do modal expandido). */
  hideToolbar?: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const { title, columns, rows } = presentation;
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);
  const [copied, setCopied] = useState(false);
  const [rowMenu, setRowMenu] = useState<{
    anchor: { x: number; y: number };
    actions: ReturnType<typeof buildTableRowMenuActions>;
  } | null>(null);

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
    <div
      className={[
        "mdc-rich-table",
        hideToolbar ? "mdc-rich-table--embedded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!hideToolbar ? (
        <div className="mdc-rich-table__header">
          {hideTitle ? (
            <span className="mdc-rich-table__title" aria-hidden="true" />
          ) : (
            <span className="mdc-rich-table__title">{title}</span>
          )}
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
            <ExpandButton presentation={presentation} onDrillDown={onDrillDown} />
          </div>
        </div>
      ) : null}

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
                onClick={(event) => {
                  if (!onDrillDown) return;

                  const actions = buildTableRowMenuActions(row, columns);

                  if (!actions.length) {
                    return;
                  }

                  setRowMenu({
                    anchor: { x: event.clientX, y: event.clientY },
                    actions,
                  });
                }}
                title={onDrillDown ? "Clique para ver ações" : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={getAlignClass(
                      col.key,
                      row[col.key],
                      col.dataType,
                      row,
                    )}
                  >
                    {formatCellValue(row[col.key], col.key, col.dataType, row)}
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

      {rowMenu && onDrillDown ? (
        <ChatTableRowMenu
          actions={rowMenu.actions}
          anchor={rowMenu.anchor}
          onSelect={onDrillDown}
          onClose={() => setRowMenu(null)}
        />
      ) : null}
    </div>
  );
}
