/** Catálogo V3 dos seis métodos de balanceamento — a fonte do plano
 * mestre define o que está implementado; métodos sem suporte exibem
 * explicação e requisitos, nunca um CTA de cálculo inerte. */

export type MethodId = "m1" | "m2" | "m3" | "m4" | "m5" | "m6";

export type MethodStatus =
  | "available"
  | "limited"
  | "implemented"
  | "planned";

export type BalancingMethod = {
  id: MethodId;
  label: string;
  name: string;
  status: MethodStatus;
  statusLabel: string;
  summary: string;
  requirements?: string[];
};

export const BALANCING_METHODS: BalancingMethod[] = [
  {
    id: "m1",
    label: "M1",
    name: "Capacidade e takt",
    status: "available",
    statusLabel: "Disponível",
    summary:
      "Takt, conteúdo de trabalho, mínimo teórico de postos e gargalo candidato — cálculo determinístico do domínio oficial.",
  },
  {
    id: "m2",
    label: "M2",
    name: "FFD / Largest Candidate Rule",
    status: "limited",
    statusLabel: "FFD limitado",
    summary:
      "Distribuição simulada por capacidade de takt sem precedência (FFD do domínio). LCR depende de precedências oficiais.",
    requirements: [
      "Precedências oficiais entre operações (não existem no contrato atual).",
    ],
  },
  {
    id: "m3",
    label: "M3",
    name: "Ranked Positional Weight",
    status: "planned",
    statusLabel: "Planejado",
    summary:
      "Priorização por peso posicional — exige grafo de precedências oficial.",
    requirements: [
      "Contrato de precedências aprovado pela Engenharia/Coordination.",
    ],
  },
  {
    id: "m4",
    label: "M4",
    name: "Kilbridge-Wester",
    status: "planned",
    statusLabel: "Planejado",
    summary:
      "Distribuição em colunas de precedência — exige grafo de precedências oficial.",
    requirements: [
      "Contrato de precedências aprovado pela Engenharia/Coordination.",
    ],
  },
  {
    id: "m5",
    label: "M5",
    name: "Yamazumi interativo",
    status: "implemented",
    statusLabel: "Nesta release",
    summary:
      "Configuração manual de postos hipotéticos com visualização de carga × takt. Análise visual — não é solver de viabilidade.",
  },
  {
    id: "m6",
    label: "M6",
    name: "Dimensionamento de recursos",
    status: "planned",
    statusLabel: "Planejado",
    summary:
      "Recursos, operadores e posições paralelas — exige contratos de capacidade e simultaneidade.",
    requirements: [
      "Contratos de capacidade de recurso e simultaneidade de operadores.",
    ],
  },
];

export const METHOD_STATUS_BADGE_VARIANT: Record<
  MethodStatus,
  "success" | "warning" | "neutral"
> = {
  available: "success",
  limited: "warning",
  implemented: "success",
  planned: "neutral",
};
