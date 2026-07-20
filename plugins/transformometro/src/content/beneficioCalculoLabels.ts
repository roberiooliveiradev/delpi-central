/** Rótulos e apresentação da categoria de cálculo de benefício (Playbook 22). */
export const BENEFICIO_CALCULO_CATEGORIA_DEFAULT = "economia_tempo";

export const BENEFICIO_CALCULO_LABELS: Record<string, string> = {
  economia_tempo: "Economia de tempo",
  reducao_volume: "Redução de execuções",
  ganho_capacidade: "Ganho de capacidade",
  economia_qualidade: "Economia de qualidade",
  misto: "Misto",
  automatico: "Automático",
};

/** Orientação de cadastro na medição, por categoria. */
export const BENEFICIO_MEDICAO_ORIENTACAO: Record<string, string> = {
  economia_tempo:
    "Compare custo com o mesmo volume da referência (1:1). Diferença de volume mistura Δtempo com Δvolume.",
  reducao_volume:
    "O benefício principal é menos execuções: informe o volume real (pode ser menor que a referência).",
  ganho_capacidade:
    "Volume acima da referência gera ganho de capacidade, somado à economia bruta e ao ROI. Os componentes de custo continuam no breakdown.",
  economia_qualidade:
    "Foque em retrabalho, erro e outros desperdícios — esses componentes já entram na economia bruta.",
  misto:
    "O motor mostra breakdown e sinais de volume; a economia bruta segue a soma dos componentes de custo.",
  automatico:
    "O sistema destaca sinais de volume e breakdown; totais financeiros (ROI) não mudam pela categoria.",
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

export function beneficioCalculoBadgeClass(value?: string | null): string {
  const key = String(value ?? "")
    .trim()
    .toLowerCase();
  switch (key) {
    case "ganho_capacidade":
      return "ds-badge ds-badge--success";
    case "reducao_volume":
      return "ds-badge ds-badge--warning";
    case "economia_qualidade":
      return "ds-badge ds-badge--info";
    case "economia_tempo":
      return "ds-badge ds-badge--info";
    case "misto":
    case "automatico":
      return "ds-badge";
    default:
      return "ds-badge";
  }
}

export function medicaoCategoriaHints(
  categoria: string | null | undefined,
  volume: number,
  volumeReferencia: number | null | undefined
): string[] {
  const cat = (categoria || BENEFICIO_CALCULO_CATEGORIA_DEFAULT).toLowerCase();
  const hints: string[] = [];
  const orientacao = BENEFICIO_MEDICAO_ORIENTACAO[cat];
  if (orientacao) hints.push(orientacao);

  if (volumeReferencia == null || !Number.isFinite(volumeReferencia)) {
    return hints;
  }
  const delta = Number(volume) - Number(volumeReferencia);
  if (Math.abs(delta) < 1e-9) return hints;

  if (cat === "economia_tempo") {
    hints.push(
      `Volume da referência: ${volumeReferencia}. Volumes diferentes misturam Δtempo com Δvolume na economia.`
    );
  } else if (cat === "ganho_capacidade" && delta <= 0) {
    hints.push(
      `Para ganho de capacidade, o volume precisa ficar acima da referência (${volumeReferencia}).`
    );
  } else if (cat === "reducao_volume" && delta >= 0) {
    hints.push(
      `Para redução de execuções, o volume precisa ficar abaixo da referência (${volumeReferencia}).`
    );
  }
  return hints;
}
