import { downloadCsv } from "./csv";

export function downloadRolSeriesCsv(
  filename: string,
  points: {
    periodo: string;
    rolMatrix: number;
    rolBranch: number;
  }[]
): void {
  if (points.length === 0) return;

  downloadCsv(
    filename,
    ["Período", "ROL Matriz (01)", "ROL Filial (02)"],
    points.map((point) => [
      point.periodo,
      String(point.rolMatrix),
      String(point.rolBranch),
    ])
  );
}
