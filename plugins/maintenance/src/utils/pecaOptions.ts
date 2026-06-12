import type { ComponenteItem, FerramentaItem } from "../data/api/maintenanceApi";

export type PecaOption = {
  codigo: string;
  descricao: string;
};

/** Prefixo canônico de código de peça (grupo 3019 no Protheus). */
export const PECA_CODIGO_PREFIX = "3019";

export function isPecaCodigo(codigo: string): boolean {
  return codigo.trim().startsWith(PECA_CODIGO_PREFIX);
}

function dedupeAndSort(options: PecaOption[]): PecaOption[] {
  const seen = new Set<string>();
  return options
    .filter((item) => {
      if (!isPecaCodigo(item.codigo) || seen.has(item.codigo)) return false;
      seen.add(item.codigo);
      return true;
    })
    .sort((first, second) => first.codigo.localeCompare(second.codigo, "pt-BR"));
}

export function ferramentasToPecaOptions(items: FerramentaItem[]): PecaOption[] {
  return dedupeAndSort(
    items.map((item) => ({
      codigo: item.codigo,
      descricao: item.descricao,
    })),
  );
}

/** Peças da estrutura do mini-aplicador (mesma origem da tabela Componentes e estoque). */
export function estruturaToPecaOptions(componentes: ComponenteItem[]): PecaOption[] {
  const seen = new Set<string>();
  return componentes
    .filter((item) => {
      const codigo = item.codigo.trim();
      if (!codigo || seen.has(codigo)) return false;
      seen.add(codigo);
      return true;
    })
    .sort((first, second) => first.codigo.localeCompare(second.codigo, "pt-BR"))
    .map((item) => ({
      codigo: item.codigo.trim(),
      descricao: item.descricao?.trim() ?? "",
    }));
}

export function componentesToPecaOptions(componentes: ComponenteItem[]): PecaOption[] {
  return dedupeAndSort(
    componentes.map((item) => ({
      codigo: item.codigo,
      descricao: item.descricao,
    })),
  );
}

export function formatPecaLabel(option: Pick<PecaOption, "codigo" | "descricao">): string {
  return formatCodigoDescricao(option.codigo, option.descricao);
}

export function formatCodigoDescricao(codigo: string, descricao?: string | null): string {
  const code = codigo.trim();
  const label = descricao?.trim();
  if (!label || label === code) return code;
  return `${code} — ${label}`;
}

/** Mapa código → descrição a partir de listas TOTVS/estrutura (ignora descrição vazia ou igual ao código). */
export function buildPecaDescricaoMap(
  sources: Array<Iterable<{ codigo: string; descricao?: string | null }>>,
): Record<string, string> {
  const map: Record<string, string> = {};
  for (const source of sources) {
    for (const item of source) {
      const codigo = item.codigo.trim();
      const descricao = item.descricao?.trim();
      if (!codigo || !descricao || descricao === codigo || map[codigo]) continue;
      map[codigo] = descricao;
    }
  }
  return map;
}

/** Peças distintas presentes no histórico de reposições (filtro do histórico). */
export function reposicoesToPecaOptions(
  reposicoes: { codigo_peca: string }[],
  descricaoByCodigo: Record<string, string> = {},
): PecaOption[] {
  const seen = new Set<string>();
  const options: PecaOption[] = [];

  for (const item of reposicoes) {
    const codigo = item.codigo_peca.trim();
    if (!codigo || seen.has(codigo)) continue;
    seen.add(codigo);
    options.push({
      codigo,
      descricao: descricaoByCodigo[codigo] ?? "",
    });
  }

  return options.sort((first, second) => first.codigo.localeCompare(second.codigo, "pt-BR"));
}
