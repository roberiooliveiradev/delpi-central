/** Slugs reservados para cadastro novo nas rotas de catálogo. */
export const CATALOG_CREATE = {
  filial: "nova",
  setor: "novo",
  recurso: "novo",
} as const;

export function isCatalogCreateId(kind: keyof typeof CATALOG_CREATE, id: string): boolean {
  return id === CATALOG_CREATE[kind];
}
