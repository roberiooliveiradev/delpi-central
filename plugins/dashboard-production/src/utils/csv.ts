/** Compat — preferir `exportMatrixToCsv` / `@delpi/plugin-ui`. */
export { exportMatrixToCsv as downloadCsvFromMatrix } from "@delpi/plugin-ui";

import { exportMatrixToCsv } from "@delpi/plugin-ui";

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
