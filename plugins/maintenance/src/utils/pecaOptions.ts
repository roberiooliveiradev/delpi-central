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
  const label = descricao?.trim();
  if (!label) return codigo;
  return `${codigo} — ${label}`;
}
