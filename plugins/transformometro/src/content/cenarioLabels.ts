/** Rótulos amigáveis (PT-BR) para slugs técnicos de cenário. */
export const CENARIO_LABELS: Record<string, string> = {
  baseline: "Linha de base (as-is)",
  melhoria: "Melhoria de processo",
  automacao: "Automação",
  correcao: "Correção / estabilização",
};

export function cenarioLabel(value?: string | null): string {
  const key = String(value ?? "")
    .trim()
    .toLowerCase();
  if (!key) return "—";
  return CENARIO_LABELS[key] ?? value ?? "—";
}

export function cenarioSelectLabel(value: string): string {
  return cenarioLabel(value);
}
