export function resolveAutoExpandedPecaCodes(
  items: Array<{ codigo: string }>,
  filters: { codigo?: string; descricao?: string },
): Set<string> {
  const codigo = filters.codigo?.trim() ?? "";
  const descricao = filters.descricao?.trim() ?? "";
  if (!codigo && !descricao) {
    return new Set();
  }
  return new Set(items.map((item) => item.codigo));
}
