import { useEffect, useMemo, useState } from "react";

import {
  prepareSpreadsheetSheet,
  spreadsheetColumnLabel,
  type SpreadsheetPreviewCell,
  type SpreadsheetPreviewData,
} from "./spreadsheetPreviewModel";

type Props = {
  data: SpreadsheetPreviewData;
};

function renderCellContent(cell: SpreadsheetPreviewCell) {
  if (cell.richParts && cell.richParts.length > 0) {
    return cell.richParts.map((part, index) => (
      <span key={index} style={part.style}>
        {part.text}
      </span>
    ));
  }

  return cell.value;
}

export function SpreadsheetPreview({ data }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeSheet = data.sheets[activeIndex] ?? data.sheets[0];

  useEffect(() => {
    setActiveIndex(0);
  }, [data]);

  const { sheet, limits } = useMemo(() => {
    if (!activeSheet) {
      return {
        sheet: {
          name: "Planilha1",
          rows: [[{ value: "" }]],
          columnWidths: [undefined],
          rowHeights: [undefined],
          hidden: false,
        },
        limits: { rowTruncated: false, colTruncated: false },
      };
    }

    const prepared = prepareSpreadsheetSheet(activeSheet);
    return prepared;
  }, [activeSheet]);

  const colCount = Math.max(...sheet.rows.map((row) => row.length), 1);

  if (!activeSheet) {
    return <p className="pac-muted pac-evidence-preview-modal__status">Planilha vazia.</p>;
  }

  return (
    <div
      className="pac-spreadsheet-preview"
      role="region"
      aria-label="Pré-visualização da planilha somente leitura"
    >
      <div className="pac-spreadsheet-preview__chrome">
        <div className="pac-spreadsheet-preview__titlebar">
          <span className="pac-spreadsheet-preview__title">Excel</span>
          <span className="pac-spreadsheet-preview__badge">Somente leitura</span>
        </div>
        <div className="pac-spreadsheet-preview__formula-bar" aria-hidden="true">
          <span className="pac-spreadsheet-preview__name-box">
            {spreadsheetColumnLabel(0)}1
          </span>
          <span className="pac-spreadsheet-preview__fx">fx</span>
          <span className="pac-spreadsheet-preview__formula-input" />
        </div>
      </div>

      <div className="pac-spreadsheet-preview__viewport">
        <table className="pac-spreadsheet-preview__grid">
          <colgroup>
            <col className="pac-spreadsheet-preview__corner-col" />
            {Array.from({ length: colCount }, (_, colIndex) => (
              <col
                key={colIndex}
                style={sheet.columnWidths[colIndex] ? { width: `${sheet.columnWidths[colIndex]}px` } : undefined}
              />
            ))}
          </colgroup>
          <thead>
            <tr>
              <th className="pac-spreadsheet-preview__corner" scope="col" aria-hidden="true" />
              {Array.from({ length: colCount }, (_, colIndex) => (
                <th
                  key={colIndex}
                  className="pac-spreadsheet-preview__col-head"
                  scope="col"
                >
                  {spreadsheetColumnLabel(colIndex)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sheet.rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                style={sheet.rowHeights[rowIndex] ? { height: `${sheet.rowHeights[rowIndex]}px` } : undefined}
              >
                <th className="pac-spreadsheet-preview__row-head" scope="row">
                  {rowIndex + 1}
                </th>
                {row.map((cell, colIndex) => {
                  if (cell.skip) return null;

                  return (
                    <td
                      key={colIndex}
                      className="pac-spreadsheet-preview__cell"
                      colSpan={cell.colspan}
                      rowSpan={cell.rowspan}
                      style={cell.style}
                    >
                      {renderCellContent(cell)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pac-spreadsheet-preview__tabs" role="tablist" aria-label="Abas da planilha">
        {data.sheets.map((tabSheet, index) => (
          <button
            key={`${index}-${tabSheet.name}`}
            type="button"
            role="tab"
            aria-selected={index === activeIndex}
            title={tabSheet.hidden ? `${tabSheet.name} (oculta no Excel)` : tabSheet.name}
            className={[
              "pac-spreadsheet-preview__tab",
              index === activeIndex ? "is-active" : "",
              tabSheet.hidden ? "is-hidden-sheet" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveIndex(index)}
          >
            {tabSheet.name}
          </button>
        ))}
      </div>

      {limits.rowTruncated || limits.colTruncated ? (
        <p className="pac-muted pac-spreadsheet-preview__truncated">
          Pré-visualização limitada
          {limits.rowTruncated ? ` a ${sheet.rows.length} linhas` : ""}
          {limits.rowTruncated && limits.colTruncated ? " e" : ""}
          {limits.colTruncated ? ` ${colCount} colunas` : ""}
          {" "}na aba «{sheet.name}». Baixe o arquivo para ver a planilha completa.
        </p>
      ) : null}
    </div>
  );
}
