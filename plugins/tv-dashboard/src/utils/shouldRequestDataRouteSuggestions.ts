/**
 * Heurística: frase com domínio+indicador → discovery owner-local (POST suggest);
 * token único curto → só substring local no catálogo.
 *
 * Limiar alinhado à VISTA: ≥ 2 tokens OU ≥ 12 caracteres
 * (ex.: «otd comercial» dispara; «oee» / «estoque» não).
 */
export function shouldRequestDataRouteSuggestions(query: string): boolean {
  const trimmed = String(query || "").trim();
  if (!trimmed) return false;
  if (trimmed.length >= 12) return true;
  const tokens = trimmed.split(/\s+/).filter(Boolean);
  return tokens.length >= 2;
}
