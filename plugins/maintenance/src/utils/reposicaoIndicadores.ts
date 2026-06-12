import type { ReposicaoItem } from "../data/api/maintenanceApi";

export type MotivoIndicador = {
  motivo_id: number;
  descricao: string;
  quantidade: number;
};

export type ReposicaoIndicadores = {
  total: number;
  pecasDistintas: number;
  mediaGolpes: number;
  ultimaReposicao: string | null;
  pecaMaisTrocada: { codigo: string; quantidade: number } | null;
  porMotivo: MotivoIndicador[];
};

const EMPTY: ReposicaoIndicadores = {
  total: 0,
  pecasDistintas: 0,
  mediaGolpes: 0,
  ultimaReposicao: null,
  pecaMaisTrocada: null,
  porMotivo: [],
};

export function computeReposicaoIndicadores(reposicoes: ReposicaoItem[]): ReposicaoIndicadores {
  if (reposicoes.length === 0) return EMPTY;

  const pecas = new Set<string>();
  const pecaCounts = new Map<string, number>();
  const motivoMap = new Map<number, { descricao: string; quantidade: number }>();
  let golpesSum = 0;
  let ultima: Date | null = null;

  for (const item of reposicoes) {
    pecas.add(item.codigo_peca);
    pecaCounts.set(item.codigo_peca, (pecaCounts.get(item.codigo_peca) ?? 0) + 1);
    golpesSum += item.golpes;

    const date = new Date(item.data_reposicao);
    if (!ultima || date.getTime() > ultima.getTime()) {
      ultima = date;
    }

    const descricao = item.motivo_descricao?.trim() || `Motivo ${item.motivo_id}`;
    const motivo = motivoMap.get(item.motivo_id);
    if (motivo) {
      motivo.quantidade += 1;
    } else {
      motivoMap.set(item.motivo_id, { descricao, quantidade: 1 });
    }
  }

  const pecaMaisTrocada =
    [...pecaCounts.entries()]
      .map(([codigo, quantidade]) => ({ codigo, quantidade }))
      .sort(
        (first, second) =>
          second.quantidade - first.quantidade ||
          first.codigo.localeCompare(second.codigo, "pt-BR"),
      )[0] ?? null;

  const porMotivo = [...motivoMap.entries()]
    .map(([motivo_id, data]) => ({ motivo_id, ...data }))
    .sort(
      (first, second) =>
        second.quantidade - first.quantidade ||
        first.descricao.localeCompare(second.descricao, "pt-BR"),
    );

  return {
    total: reposicoes.length,
    pecasDistintas: pecas.size,
    mediaGolpes: Math.round(golpesSum / reposicoes.length),
    ultimaReposicao: ultima?.toISOString() ?? null,
    pecaMaisTrocada,
    porMotivo,
  };
}

export function formatReposicaoIndicadorDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
