/**
 * Comparação profunda estável para drafts de formulário (objetos/arrays JSON-serializáveis).
 * Uso canônico com `useEditableDraft` e `EditableSectionCard.dirty`.
 */

function stableStringify(value: unknown): string {
  return JSON.stringify(value, (_key, current) => {
    if (!current || typeof current !== "object" || Array.isArray(current)) {
      return current;
    }
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(current as Record<string, unknown>).sort()) {
      sorted[key] = (current as Record<string, unknown>)[key];
    }
    return sorted;
  });
}

export function valuesEqual(a: unknown, b: unknown): boolean {
  if (Object.is(a, b)) return true;
  try {
    return stableStringify(a) === stableStringify(b);
  } catch {
    return false;
  }
}

/** Exibe botão Salvar só com alterações (ou enquanto salva, para feedback). */
export function shouldShowDirtySave(dirty: boolean, saving = false): boolean {
  return Boolean(dirty || saving);
}
