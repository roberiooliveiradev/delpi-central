const ESCOPO_RECURSO_LABELS: Record<string, string> = {
  empresa: "Empresa (pool global)",
  filial: "Unidade (mesma unidade da instância)",
  setor: "Departamento (mesmo departamento da instância)",
};

export function labelEscopoRecurso(value?: string | null): string {
  if (!value) return "Empresa (pool global)";
  return ESCOPO_RECURSO_LABELS[value] ?? value;
}

const CRITERIO_RATEIO_LABELS: Record<string, string> = {
  igualitario: "Igualitário entre vínculos",
  por_revisoes_ativas: "Por revisões ativas",
  por_peso: "Por peso do vínculo",
};

const BASE_COMPETENCIA_LABELS: Record<string, string> = {
  mensal_cheio: "Mensal cheio",
  proporcional_dias: "Proporcional aos dias",
};

export function labelCriterioRateio(value?: string | null): string {
  if (!value) return "—";
  return CRITERIO_RATEIO_LABELS[value] ?? value;
}

export function labelBaseCompetencia(value?: string | null): string {
  if (!value) return "Mensal cheio";
  return BASE_COMPETENCIA_LABELS[value] ?? value;
}

export function labelSimNao(value: boolean | undefined): string {
  if (value === undefined) return "—";
  return value ? "Sim" : "Não";
}

const TIPO_INVESTIMENTO_LABELS: Record<string, string> = {
  fixo: "Fixo",
  variavel: "Variável",
  recorrente: "Recorrente",
  unico: "Único",
};

const CATEGORIA_INVESTIMENTO_LABELS: Record<string, string> = {
  software: "Software",
  treinamento: "Treinamento",
  consultoria: "Consultoria",
  equipamento: "Equipamento",
  horas_internas: "Horas internas",
  terceiros: "Terceiros",
};

const RECORRENCIA_LABELS: Record<string, string> = {
  unico: "Único",
  mensal: "Mensal",
  anual: "Anual",
};

export function labelTipoInvestimento(value?: string | null): string {
  if (!value) return "—";
  return TIPO_INVESTIMENTO_LABELS[value] ?? value;
}

export function labelCategoriaInvestimento(value?: string | null): string {
  if (!value) return "—";
  return CATEGORIA_INVESTIMENTO_LABELS[value] ?? value;
}

export function labelRecorrencia(value?: string | null): string {
  if (!value) return "—";
  return RECORRENCIA_LABELS[value] ?? value;
}
