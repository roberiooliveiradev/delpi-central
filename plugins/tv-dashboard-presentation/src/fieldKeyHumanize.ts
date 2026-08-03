/**
 * Humanização centralizada de chaves snake_case / camelCase → rótulo PT.
 *
 * Cascata:
 *   1. mapa de chave completa (rótulo curado)
 *   2. tokens (`_` / camelCase = espaço) traduzidos + primeira letra maiúscula
 *
 * Usado quando catálogo/meta não trazem label — evita `gross_savings_month` /
 * `valorDia` grudado (`Valordia`) no picker.
 */

/** Rótulos canônicos por chave completa (preferir sempre que existir). */
export const FIELD_KEY_LABELS: Record<string, string> = {
  month: "Mês",
  periodo: "Período",
  value: "Valor",
  total: "Total",
  gross_savings_month: "Economia bruta (mês)",
  gross_costs_month: "Custos brutos (mês)",
  gross_investment_month: "Investimento bruto (mês)",
  gross_recurring_investment_month: "Invest. recorrente (mês)",
  shared_resource_cost_month: "Custo recurso compartilhado (mês)",
  investment_total_month: "Investimento total (mês)",
  net_savings_month: "Economia líquida (mês)",
  implemented_solutions_count: "Soluções ativas",
  solutions_started_in_period_count: "Soluções iniciadas no período",
  total_investment_in_period: "Investimento total",
  total_gross_costs_until_now: "Investimento total",
  total_gross_savings_in_period: "Economia bruta",
  total_hours_saved_until_now: "Horas economizadas",
  total_net_savings_until_now: "Economia líquida",
  average_roi: "ROI médio",
  accumulated_net_savings_until_now: "Economia líquida acumulada",
  economia_bruta: "Economia bruta",
  investimento: "Investimento",
  economia_liquida: "Economia líquida",
  horas_economizadas: "Horas economizadas",
  goal: "Meta",
  goal_value: "Valor da meta",
  goal_label: "Meta",
  goal_periodicity: "Periodicidade da meta",
  goal_mode: "Modo da meta",
  goal_scope_branch: "Filial da meta",
  goal_scope_label: "Escopo da meta",
  goal_scope_hint: "Observação da meta",
  comparable_goal: "Meta",
  valor_dia: "Valor dia",
  total_quantidade: "Total quantidade",
  total_valor: "Total valor",
  registros_sem_custo: "Registros sem custo",
  ocorrencias: "Ocorrências",
};

/**
 * Tradução de tokens individuais (snake_case / camelCase).
 * Ordem do inglês é preservada; chave completa no mapa acima cobre frases naturais.
 */
export const FIELD_TOKEN_LABELS: Record<string, string> = {
  month: "mês",
  months: "meses",
  year: "ano",
  years: "anos",
  day: "dia",
  days: "dias",
  dia: "dia",
  week: "semana",
  period: "período",
  periodo: "período",
  date: "data",
  start: "início",
  end: "fim",
  from: "de",
  to: "até",
  gross: "bruto",
  net: "líquido",
  savings: "economia",
  saving: "economia",
  costs: "custos",
  cost: "custo",
  custo: "custo",
  investment: "investimento",
  investments: "investimentos",
  recurring: "recorrente",
  shared: "compartilhado",
  resource: "recurso",
  resources: "recursos",
  hours: "horas",
  hour: "hora",
  saved: "economizadas",
  total: "total",
  average: "média",
  avg: "média",
  mean: "média",
  count: "quantidade",
  quantity: "quantidade",
  quantidade: "quantidade",
  qty: "qtd.",
  amount: "valor",
  value: "valor",
  values: "valores",
  valor: "valor",
  rate: "taxa",
  pct: "%",
  percent: "%",
  percentage: "%",
  roi: "ROI",
  goal: "meta",
  target: "meta",
  branch: "filial",
  filial: "filial",
  sector: "setor",
  department: "departamento",
  product: "produto",
  item: "item",
  code: "código",
  name: "nome",
  description: "descrição",
  status: "status",
  active: "ativas",
  started: "iniciadas",
  solutions: "soluções",
  solution: "solução",
  implemented: "implementadas",
  in: "no",
  until: "até",
  now: "agora",
  accumulated: "acumulada",
  shared_resource: "recurso compartilhado",
  registros: "registros",
  registro: "registro",
  sem: "sem",
  ocorrencias: "ocorrências",
  ocorrencia: "ocorrência",
};

/**
 * Quebra `valor_dia` / `valorDia` / `ValorDia` em tokens minúsculos.
 * Sem isso, camelCase vira um único token e o rótulo fica grudado (`Valordia`).
 */
export function splitFieldKeyTokens(field: string): string[] {
  const raw = String(field ?? "").trim();
  if (!raw) return [];
  const withBreaks = raw
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .replace(/([a-zA-Z])([0-9])/g, "$1_$2")
    .replace(/([0-9])([a-zA-Z])/g, "$1_$2");
  return withBreaks
    .toLowerCase()
    .split(/[_-\s]+/)
    .filter(Boolean);
}

/** Forma canônica snake_case para lookup no mapa de chave completa. */
export function normalizeFieldKeySnake(field: string): string {
  return splitFieldKeyTokens(field).join("_");
}

/** Label fraco: igual à chave, só `_`→espaço, ou chave colapsada sem espaços (grudado). */
export function isWeakFieldLabel(field: string, label: string | null | undefined): boolean {
  const key = String(field ?? "").trim();
  const text = String(label ?? "").trim();
  if (!key) return !text;
  if (!text) return true;
  if (text === key) return true;
  const spaced = splitFieldKeyTokens(key).join(" ");
  if (text === spaced) return true;
  if (text.toLowerCase() === spaced.toLowerCase()) return true;
  if (text.toLowerCase() === key.toLowerCase()) return true;
  const collapsedKey = splitFieldKeyTokens(key).join("");
  const collapsedLabel = text.replace(/\s+/g, "").toLowerCase();
  /* Rótulo grudado: mesma letras da chave, mas sem espaços entre tokens. */
  if (
    collapsedKey &&
    collapsedLabel === collapsedKey &&
    splitFieldKeyTokens(key).length > 1 &&
    !/\s/.test(text)
  ) {
    return true;
  }
  return false;
}

function capitalizeFirst(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Converte `gross_savings_month` / `valorDia` → rótulo PT com espaços.
 * Preferência: chave completa; senão tokens traduzidos unidos por espaço.
 */
export function humanizeFieldKey(field: string): string {
  const key = String(field ?? "").trim();
  if (!key) return "";
  const snake = normalizeFieldKeySnake(key);
  const curated = FIELD_KEY_LABELS[snake] ?? FIELD_KEY_LABELS[key.toLowerCase()];
  if (curated) return curated;

  const tokens = splitFieldKeyTokens(key);
  if (tokens.length === 0) return key;
  if (tokens.length === 1) {
    const single = FIELD_TOKEN_LABELS[tokens[0]!] ?? tokens[0]!;
    return capitalizeFirst(single);
  }

  const translated = tokens.map((token) => FIELD_TOKEN_LABELS[token] ?? token);
  return capitalizeFirst(translated.join(" "));
}

/**
 * Catálogo de campos a partir de valueFields + valueFieldLabels (todas as chaves rotuladas).
 * Garante que labels de colunas descobertas (ex.: monthly_breakdown) cheguem ao picker.
 */
export function catalogFieldsFromRouteLabels(
  valueFields?: readonly string[] | null,
  valueFieldLabels?: Record<string, string> | null,
): Array<{ field: string; label: string }> {
  const labels = valueFieldLabels ?? {};
  const fields = new Set<string>();
  for (const field of valueFields ?? []) {
    const key = String(field).trim();
    if (key) fields.add(key);
  }
  for (const field of Object.keys(labels)) {
    const key = String(field).trim();
    if (key) fields.add(key);
  }
  return [...fields].map((field) => {
    const curated = labels[field]?.trim();
    return {
      field,
      label:
        curated && !isWeakFieldLabel(field, curated) ? curated : humanizeFieldKey(field),
    };
  });
}
