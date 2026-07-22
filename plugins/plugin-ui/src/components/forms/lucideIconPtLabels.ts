/**
 * Rótulos e aliases de busca em português para ícones Lucide (kebab-case).
 * Fonte canônica: `src/content/lucide-icon-pt-BR.json`
 * (gerar/atualizar com `node scripts/generate-lucide-icon-pt-BR.mjs`).
 */

import catalog from "../../content/lucide-icon-pt-BR.json";

type LucideIconPtCatalog = {
  labels: Record<string, string>;
  aliases: Record<string, string[]>;
};

const ptCatalog = catalog as LucideIconPtCatalog;

export const LUCIDE_ICON_PT_LABELS: Readonly<Record<string, string>> = Object.freeze({
  ...ptCatalog.labels,
});

/** Termos PT extras que apontam para o kebab do ícone. */
export const LUCIDE_ICON_PT_ALIASES: Readonly<Record<string, readonly string[]>> = Object.freeze(
  Object.fromEntries(
    Object.entries(ptCatalog.aliases ?? {}).map(([kebab, aliases]) => [
      kebab,
      Object.freeze([...(aliases ?? [])]),
    ]),
  ),
);

/** Quantidade de rótulos no catálogo JSON (para testes / diagnóstico). */
export function countLucideIconPtLabels(): number {
  return Object.keys(LUCIDE_ICON_PT_LABELS).length;
}
