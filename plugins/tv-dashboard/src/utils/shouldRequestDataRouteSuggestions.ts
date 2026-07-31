/**
 * Heurística v1: frase operacional → S2S suggest; texto curto → só substring local.
 * Limiar: ≥ 16 caracteres OU ≥ 3 tokens.
 */
export function shouldRequestDataRouteSuggestions(query: string): boolean {
  const trimmed = String(query || "").trim();
  if (!trimmed) return false;
  if (trimmed.length >= 16) return true;
  const tokens = trimmed.split(/\s+/).filter(Boolean);
  return tokens.length >= 3;
}
