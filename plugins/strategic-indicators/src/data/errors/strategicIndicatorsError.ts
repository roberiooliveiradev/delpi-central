export type StrategicIndicatorsErrorContext = {
  surface: string;
  route?: string;
  method?: string;
  httpStatus?: number;
  competence?: string | null;
  branch?: string | null;
  departmentId?: string | null;
};

export type StrategicIndicatorsErrorView = {
  title: string;
  summary: string;
  context: StrategicIndicatorsErrorContext;
  causes: string[];
  suggestions: string[];
  technicalDetail?: string;
  rawMessage: string;
};

export type StrategicIndicatorsErrorMode = "load" | "refresh";

export class StrategicIndicatorsApiError extends Error {
  readonly view: StrategicIndicatorsErrorView;

  constructor(view: StrategicIndicatorsErrorView) {
    super(view.summary);
    this.name = "StrategicIndicatorsApiError";
    this.view = view;
  }
}

function normalizeWhitespace(value: string) {
  return value.replace(/\s+/g, " ").trim();
}

function stripKnownPrefixes(message: string) {
  return message
    .replace(/^Falha ao carregar [^:]+:\s*/i, "")
    .replace(/^Erro ao carregar [^:]+:\s*/i, "")
    .trim();
}

function detectCauses(technicalDetail: string): string[] {
  const normalized = technicalDetail.toLowerCase();
  const causes: string[] = [];

  if (
    normalized.includes("nonetype") &&
    (normalized.includes("'<' not supported") ||
      normalized.includes("not supported between"))
  ) {
    causes.push(
      "O servidor tentou comparar indicadores sem nota (período sem medição) ao montar alertas ou rankings.",
    );
  }

  if (normalized.includes("timeout") || normalized.includes("timed out")) {
    causes.push("A requisição excedeu o tempo limite de resposta da API.");
  }

  if (
    normalized.includes("connection") ||
    normalized.includes("network") ||
    normalized.includes("failed to fetch")
  ) {
    causes.push("Falha de rede ou indisponibilidade do serviço no gateway.");
  }

  if (normalized.includes("401") || normalized.includes("unauthorized")) {
    causes.push("Sessão expirada ou token de autenticação inválido.");
  }

  if (normalized.includes("403") || normalized.includes("forbidden")) {
    causes.push("Usuário sem permissão para acessar este recurso do módulo.");
  }

  if (normalized.includes("502") || normalized.includes("503")) {
    causes.push("API Indicadores Estratégicos indisponível ou reiniciando.");
  }

  if (
    normalized.includes("fetch_all") ||
    normalized.includes("fetch_one") ||
    normalized.includes("banco de plugins")
  ) {
    causes.push(
      "Falha ao consultar catálogo, metas ou cache no Postgres do módulo (plugins).",
    );
  }

  if (
    normalized.includes("does not exist") ||
    normalized.includes("undefinedcolumn")
  ) {
    causes.push(
      "Schema do Strategic Indicators incompleto ou API desatualizada em relação ao banco.",
    );
  }

  if (normalized.includes("character varying = date")) {
    causes.push(
      "Bug na resolução de metas por filial no backend — implante a versão corrigida da API SI.",
    );
  }

  if (!causes.length && technicalDetail) {
    causes.push("Erro interno retornado pela API ao processar o período selecionado.");
  }

  return causes;
}

function buildSuggestions(
  context: StrategicIndicatorsErrorContext,
  causes: string[],
): string[] {
  const suggestions = new Set<string>();

  if (context.competence) {
    suggestions.add(
      `Confirme se há dados publicados na planilha/fontes para a competência ${context.competence}.`,
    );
  }

  if (context.branch) {
    suggestions.add(
      `Teste a visão consolidada ou outra filial — a filial "${context.branch}" pode não ter medição no período.`,
    );
  }

  if (causes.some((item) => item.includes("sem nota"))) {
    suggestions.add(
      "Indicadores marcados como “Sem dados preenchidos” não devem derrubar o painel; se o erro persistir, atualize a API SI no servidor.",
    );
  }

  if (causes.some((item) => item.includes("rede") || item.includes("indisponível"))) {
    suggestions.add("Verifique se o container delpi-strategic-indicators-api está em execução.");
  }

  if (causes.some((item) => item.includes("autenticação"))) {
    suggestions.add("Faça logout/login no portal e tente novamente.");
  }

  if (
    causes.some(
      (item) =>
        item.includes("Schema") ||
        item.includes("catálogo") ||
        item.includes("Postgres do módulo"),
    )
  ) {
    suggestions.add(
      "No servidor: docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up",
    );
    suggestions.add(
      "Depois: docker exec delpi-strategic-indicators-api python3 -u scripts/refresh_period_scores.py",
    );
  }

  if (causes.some((item) => item.includes("metas por filial"))) {
    suggestions.add(
      "Atualize e reinicie o container strategic-indicators-api com o patch de metas por filial.",
    );
  }

  suggestions.add("Use “Tentar novamente” após corrigir a fonte ou atualizar o backend.");

  return [...suggestions];
}

export function parseStrategicIndicatorsError(
  rawMessage: string,
  context: StrategicIndicatorsErrorContext,
): StrategicIndicatorsErrorView {
  const technicalDetail = normalizeWhitespace(stripKnownPrefixes(rawMessage));
  const causes = detectCauses(technicalDetail);
  const suggestions = buildSuggestions(context, causes);

  const summary =
    causes[0] ??
    `Não foi possível carregar ${context.surface.toLowerCase()}.`;

  return {
    title: `Falha em ${context.surface}`,
    summary,
    context,
    causes,
    suggestions,
    technicalDetail: technicalDetail || undefined,
    rawMessage,
  };
}

export function toStrategicIndicatorsErrorView(
  error: unknown,
  context: StrategicIndicatorsErrorContext,
): StrategicIndicatorsErrorView {
  if (error instanceof StrategicIndicatorsApiError) {
    return error.view;
  }

  if (error instanceof Error) {
    return parseStrategicIndicatorsError(error.message, context);
  }

  return parseStrategicIndicatorsError("Erro inesperado no módulo.", context);
}

export function withStrategicIndicatorsErrorMode(
  view: StrategicIndicatorsErrorView,
  mode: StrategicIndicatorsErrorMode,
): StrategicIndicatorsErrorView {
  if (mode === "refresh") {
    return {
      ...view,
      title: `Falha ao atualizar ${view.context.surface.toLowerCase()}`,
    };
  }

  return {
    ...view,
    title: `Falha em ${view.context.surface}`,
  };
}

export function formatStrategicIndicatorsErrorLocation(
  view: StrategicIndicatorsErrorView,
): string {
  const { context } = view;
  const parts = [
    context.route,
    context.competence,
    context.branch,
    context.departmentId,
  ].filter(Boolean);

  return parts.length ? parts.join(" · ") : "—";
}
