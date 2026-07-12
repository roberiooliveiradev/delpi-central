import type { FocusEvent } from "react";

import type { ComunicadoCanvasTableBlock } from "./comunicadoTypes";

type Props = {
  block: ComunicadoCanvasTableBlock;
  editable?: boolean;
  onCellChange?: (row: number, col: number, value: string) => void;
};

export function ComunicadoCanvasTableView({ block, editable = false, onCellChange }: Props) {
  function commitCell(event: FocusEvent<HTMLTableCellElement>, row: number, col: number) {
    const value = event.currentTarget.textContent ?? "";
    if (value !== block.cells[row]?.[col]) onCellChange?.(row, col, value);
  }

  return (
    <div className="td-canvas-table" data-header-row={block.headerRow ? "true" : "false"}>
      <table>
        <tbody>
          {block.cells.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, colIndex) => {
                const Cell = block.headerRow && rowIndex === 0 ? "th" : "td";
                return (
                  <Cell
                    key={colIndex}
                    contentEditable={editable}
                    suppressContentEditableWarning
                    onBlur={(event) => commitCell(event, rowIndex, colIndex)}
                    onPointerDown={editable ? (event) => event.stopPropagation() : undefined}
                  >
                    {cell}
                  </Cell>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
