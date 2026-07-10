/** Compat — preferir `exportMatrixToCsv` / `@delpi/plugin-ui`. */
import { exportMatrixToCsv } from "@delpi/plugin-ui/index";

export { exportMatrixToCsv as downloadCsvFromMatrix };

/**
 * Legacy: headers/rows → CSV via motor shared (`;` + BOM).
 * Filename pode incluir `.csv`.
 */
export function downloadCsv(
  filename: string,
  headers: string[],
  rows: string[][],
): void {
  exportMatrixToCsv(
    {
      title: filename,
      headers,
      rows,
    },
    filename,
  );
}
