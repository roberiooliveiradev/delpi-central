/** Rótulos amigáveis (PT-BR) para categoria de cálculo de benefício (Playbook 22). */
export const BENEFICIO_CALCULO_CATEGORIA_DEFAULT = "economia_tempo";

export const BENEFICIO_CALCULO_LABELS: Record<string, string> = {
  economia_tempo: "Economia de tempo",
  reducao_volume: "Redução de execuções",
  ganho_capacidade: "Ganho de capacidade",
  economia_qualidade: "Economia de qualidade",
  misto: "Misto",
  automatico: "Automático",
};

export function beneficioCalculoLabel(value?: string | null): string {
  const key = String(value ?? "")
    .trim()
    .toLowerCase();
  if (!key) return "—";
  return BENEFICIO_CALCULO_LABELS[key] ?? value ?? "—";
}

export function beneficioCalculoSelectLabel(value: string): string {
  return beneficioCalculoLabel(value);
}
