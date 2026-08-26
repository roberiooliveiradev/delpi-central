import type { TableExportPayload } from "@delpi/plugin-ui/index";

import type { ReposicaoItem } from "../data/api/maintenanceApi";
import { formatCodigoDescricao } from "./pecaOptions";

function formatEventLabel(value: string): string {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function buildReposicoesGolpesExportPayload(
  reposicoes: ReposicaoItem[],
  pecaLabels: Record<string, string> = {},
): TableExportPayload {
  const sorted = [...reposicoes].sort(
    (first, second) =>
      new Date(first.data_reposicao).getTime() - new Date(second.data_reposicao).getTime(),
  );
  const pecas = [...new Set(sorted.map((item) => item.codigo_peca))].sort((a, b) =>
    a.localeCompare(b, "pt-BR"),
  );

  const columns = [
    { key: "data", label: "Data da reposição" },
    ...pecas.map((codigo) => ({
      key: codigo,
      label: pecaLabels[codigo]
        ? formatCodigoDescricao(codigo, pecaLabels[codigo])
        : codigo,
    })),
  ];

  const rows = sorted.map((item) => {
    const row: Record<string, string | number> = {
      data: formatEventLabel(item.data_reposicao),
    };
    for (const peca of pecas) {
      row[peca] = item.codigo_peca === peca ? item.golpes : "";
    }
    return row;
  });

  return {
    title: "Golpes por reposição",
    columns,
    rows,
  };
}
