/**
 * Serialização estável para comparação semântica de config.
 *
 * `JSON.stringify` é sensível à ordem das chaves — dois objetos semanticamente
 * iguais produzem strings diferentes quando construídos por caminhos
 * distintos (normalização backend vs sync local), gerando writes no-op que
 * bumpam `playlists.revision` sem mudança material (NOOP_REVISION_BUMP).
 */

type JsonLike = null | boolean | number | string | JsonLike[] | { [k: string]: JsonLike };

function normalize(value: unknown): JsonLike {
  if (value === null || value === undefined) return null;
  const t = typeof value;
  if (t === "boolean" || t === "string") return value as boolean | string;
  if (t === "number") return Number.isFinite(value as number) ? (value as number) : null;
  if (Array.isArray(value)) return value.map(normalize);
  if (t === "object") {
    const out: Record<string, JsonLike> = {};
    for (const key of Object.keys(value as Record<string, unknown>).sort()) {
      const raw = (value as Record<string, unknown>)[key];
      // JSON.stringify omite chaves undefined — comparar do mesmo jeito.
      if (raw === undefined) continue;
      out[key] = normalize(raw);
    }
    return out;
  }
  return null;
}

/** Igualdade semântica: mesmo conteúdo independente de ordem de chaves. */
export function stableSerialize(value: unknown): string {
  return JSON.stringify(normalize(value));
}

export function stableEquals(a: unknown, b: unknown): boolean {
  return stableSerialize(a) === stableSerialize(b);
}
