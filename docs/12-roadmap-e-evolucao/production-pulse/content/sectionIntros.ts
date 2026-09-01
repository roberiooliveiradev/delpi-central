/**
 * Copy visível abaixo dos títulos de seção (prosa curta).
 * Helps técnicos (hover ?) ficam em helpTooltips.ts — PP_HELP.
 * Copiar para plugins/production-pulse/src/content/ no scaffold E5.S1.
 */
export const PP_SECTION_INTROS = {
  form: {
    device:
      "Informe o hardware na rede. O driver define o que será medido (golpes, rotação, temperatura).",
    placement:
      "Onde o sensor está instalado. CT TOTVS só é obrigatório para postos PCP.",
    totvsDetails:
      "Opcional. Facilita cruzar com fila e apontamento do PCP.",
  },
  operator: {
    hub: "Toque no local onde você vai trabalhar. A escolha fica salva neste tablet.",
  },
  detail: {
    history:
      "Leituras gravadas automaticamente pelo intervalo de poll ou por comando manual.",
  },
  panel: {
    devices:
      "Visão consolidada dos dispositivos IoT da filial. Use filtros para encontrar postos, máquinas ou equipamentos.",
  },
} as const;

export function getPpSectionIntro(path: string): string | undefined {
  const parts = path.split(".");
  let cur: unknown = PP_SECTION_INTROS;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object" || !(p in cur)) return undefined;
    cur = (cur as Record<string, unknown>)[p];
  }
  return typeof cur === "string" ? cur : undefined;
}
