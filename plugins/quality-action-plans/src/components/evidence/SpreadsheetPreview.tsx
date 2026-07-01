import { useEffect, useMemo, useState } from "react";

import {
  prepareSpreadsheetSheet,
  spreadsheetColumnLabel,
  type SpreadsheetPreviewData,
} from "./spreadsheetPreviewModel";

type Props = {
  data: SpreadsheetPreviewData;
};

export function SpreadsheetPreview({ data }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeSheet = data.sheets[activeIndex] ?? data.sheets[0];

  useEffect(() => {
    setActiveIndex(0);
  }, [data]);

  const { rows, colCount, limits } = useMemo(() => {
    if (!activeSheet) {
      return {
        rows: [[""]],
        colCount: 1,
        limits: { rowTruncated: false, colTruncated: false },
      };
    }

    const prepared = prepareSpreadsheetSheet(activeSheet.rows);
    return {
      rows: prepared.rows,
      colCount: Math.max(...prepared.rows.map((row) => row.length), 1),
      limits: prepared.limits,
    };
  }, [activeSheet]);

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
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                <th className="pac-spreadsheet-preview__row-head" scope="row">
                  {rowIndex + 1}
                </th>
                {Array.from({ length: colCount }, (_, colIndex) => (
                  <td key={colIndex} className="pac-spreadsheet-preview__cell">
                    {row[colIndex] ?? ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pac-spreadsheet-preview__tabs" role="tablist" aria-label="Abas da planilha">
        {data.sheets.map((sheet, index) => (
          <button
            key={`${index}-${sheet.name}`}
            type="button"
            role="tab"
            aria-selected={index === activeIndex}
            title={sheet.hidden ? `${sheet.name} (oculta no Excel)` : sheet.name}
            className={[
              "pac-spreadsheet-preview__tab",
              index === activeIndex ? "is-active" : "",
              sheet.hidden ? "is-hidden-sheet" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setActiveIndex(index)}
          >
            {sheet.name}
          </button>
        ))}
      </div>

      {limits.rowTruncated || limits.colTruncated ? (
        <p className="pac-muted pac-spreadsheet-preview__truncated">
          Pré-visualização limitada
          {limits.rowTruncated ? ` a ${rows.length} linhas` : ""}
          {limits.rowTruncated && limits.colTruncated ? " e" : ""}
          {limits.colTruncated ? ` ${colCount} colunas` : ""}
          {" "}na aba «{activeSheet.name}». Baixe o arquivo para ver a planilha completa.
        </p>
      ) : null}
    </div>
  );
}
