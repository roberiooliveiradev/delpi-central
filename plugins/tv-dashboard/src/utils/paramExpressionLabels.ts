/**
 * Typed param expressions — camada de APRESENTAÇÃO (labels amigáveis,
 * resumo legível, templates de authoring). Nunca avalia nem altera o
 * contrato: o identificador persistido é sempre o nome canônico da função.
 */

import type {
  ParamExpressionAst,
  ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

import {
  EXPRESSION_BINARY_OPERATORS,
  PARAM_REF_PREFIX,
  readExpressionAst,
  type ParamExpressionNodeKind,
} from "./paramExpressions";

export type ExpressionFunctionCategoryId = "dates" | "numbers" | "text" | "lists" | "other";

export const EXPRESSION_FUNCTION_CATEGORY_LABELS: Record<
  ExpressionFunctionCategoryId,
  string
> = {
  dates: "Datas",
  numbers: "Números",
  text: "Texto",
  lists: "Listas",
  other: "Outras",
};

/** Labels de produto por função canônica — só apresentação. */
const FRIENDLY_FUNCTION_LABELS: Record<string, string> = {
  "Date.AddDays": "Adicionar dias",
  "Date.AddMonths": "Adicionar meses",
  "Date.AddWeeks": "Adicionar semanas",
  "Date.AddYears": "Adicionar anos",
  "Date.Day": "Dia do mês",
  "Date.DayOfWeek": "Dia da semana",
  "Date.EndOfMonth": "Fim do mês",
  "Date.EndOfQuarter": "Fim do trimestre",
  "Date.EndOfWeek": "Fim da semana",
  "Date.EndOfYear": "Fim do ano",
  "Date.IsWeekend": "É fim de semana",
  "Date.Month": "Mês",
  "Date.StartOfMonth": "Início do mês",
  "Date.StartOfQuarter": "Início do trimestre",
  "Date.StartOfWeek": "Início da semana",
  "Date.StartOfYear": "Início do ano",
  "Date.WeekOfYear": "Semana do ano",
  "Date.Year": "Ano",
  "Number.Abs": "Valor absoluto",
  "Number.Round": "Arredondar",
  "Number.RoundDown": "Arredondar para baixo",
  "Number.RoundUp": "Arredondar para cima",
  "Text.Length": "Comprimento do texto",
  "Text.Lower": "Minúsculas",
  "Text.Proper": "Iniciais maiúsculas",
  "Text.Trim": "Remover espaços",
  "Text.Upper": "Maiúsculas",
  "List.Average": "Média da lista",
  "List.Count": "Quantidade de itens",
  "List.First": "Primeiro item",
  "List.Last": "Último item",
  "List.Max": "Maior valor",
  "List.Min": "Menor valor",
  "List.Sum": "Soma da lista",
};

/** Fallback: prefixo `Date.`/`Number.`/`Text.`/`List.` da assinatura canônica. */
export function expressionFunctionCategory(name: string): ExpressionFunctionCategoryId {
  const prefix = String(name).split(".")[0]?.toLowerCase() ?? "";
  if (prefix === "date" || prefix === "datetime" || prefix === "duration") return "dates";
  if (prefix === "number" || prefix === "math") return "numbers";
  if (prefix === "text") return "text";
  if (prefix === "list" || prefix === "array" || prefix === "table") return "lists";
  return "other";
}

/** Label amigável; fallback = nome canônico (nunca esconde a capability). */
export function friendlyFunctionLabel(name: string): string {
  return FRIENDLY_FUNCTION_LABELS[name] ?? name;
}

export function friendlyFunctionReturnTypeLabel(returnType: string | null): string {
  switch (returnType) {
    case "date":
      return "data";
    case "datetime":
      return "data e hora";
    case "number":
      return "número";
    case "logical":
    case "boolean":
      return "verdadeiro/falso";
    case "text":
      return "texto";
    case "list":
      return "lista";
    default:
      return returnType ?? "";
  }
}

const CONTEXT_REF_LABELS: Record<string, string> = {
  today: "Hoje",
  now: "Agora",
};

const BINARY_OP_TEXT: Record<string, string> = {
  "&": "concatenado com",
  "*": "×",
  "+": "+",
  "-": "−",
  "/": "÷",
  "<": "<",
  "<=": "≤",
  "<>": "≠",
  "=": "=",
  ">": ">",
  ">=": "≥",
  and: "e",
  or: "ou",
};

const UNARY_OP_TEXT: Record<string, string> = {
  "+": "+",
  "-": "−",
  not: "não",
};

function literalCanonicalText(value: unknown): string {
  if (value === undefined) return "?";
  if (value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  return String(value);
}

function literalFriendlyText(value: unknown): string {
  if (value === undefined) return "valor vazio";
  if (value === null) return "nulo";
  if (value === true) return "Sim";
  if (value === false) return "Não";
  if (typeof value === "number") return String(value);
  const text = String(value);
  return text.trim() ? `"${text}"` : "texto vazio";
}

/** Texto canônico do AST (`Date.StartOfMonth(Date.AddMonths(today, -12))`). */
export function expressionCanonicalText(node: ParamExpressionAst | null): string {
  if (!node) return "";
  const children = node.children ?? [];
  switch (node.kind) {
    case "literal":
      return literalCanonicalText(node.value);
    case "identifier":
      return String(node.value ?? "");
    case "call":
      return `${String(node.value ?? "?")}(${children
        .map((child) => expressionCanonicalText(child))
        .join(", ")})`;
    case "binary":
      return `${expressionCanonicalText(children[0] ?? null)} ${String(
        node.value ?? "?",
      )} ${expressionCanonicalText(children[1] ?? null)}`;
    case "unary":
      return `${String(node.value ?? "")}${node.value === "not" ? " " : ""}${expressionCanonicalText(children[0] ?? null)}`;
    case "if":
      return `If(${children
        .map((child) => expressionCanonicalText(child))
        .join(", ")})`;
    case "list":
      return `[${children.map((child) => expressionCanonicalText(child)).join(", ")}]`;
    default:
      return String(node.value ?? "");
  }
}

const SUMMARY_MAX_DEPTH = 6;

/**
 * Resumo legível — só padrões seguros; fora deles devolve o texto canônico.
 * Nunca avalia: é derivação puramente estrutural do AST.
 */
export function summarizeExpressionAst(
  node: ParamExpressionAst | null,
  depth = 0,
): string {
  if (!node) return "Expressão vazia";
  if (depth > SUMMARY_MAX_DEPTH) return expressionCanonicalText(node);
  const children = node.children ?? [];
  const sub = (index: number) => summarizeExpressionAst(children[index] ?? null, depth + 1);
  switch (node.kind) {
    case "literal":
      return literalFriendlyText(node.value);
    case "identifier": {
      const id = String(node.value ?? "");
      if (CONTEXT_REF_LABELS[id]) return CONTEXT_REF_LABELS[id];
      if (id.startsWith(PARAM_REF_PREFIX)) {
        return `Parâmetro ${id.slice(PARAM_REF_PREFIX.length)}`;
      }
      return id;
    }
    case "call": {
      const name = String(node.value ?? "");
      const friendly = FRIENDLY_FUNCTION_LABELS[name];
      if (name === "Date.AddMonths" || name === "Date.AddDays" || name === "Date.AddYears") {
        const amount = children[1]?.kind === "literal" ? Number(children[1].value) : NaN;
        const unit =
          name === "Date.AddMonths" ? "mês|meses" : name === "Date.AddDays" ? "dia|dias" : "ano|anos";
        if (Number.isFinite(amount)) {
          const [singular, plural] = unit.split("|");
          const abs = Math.abs(amount);
          const base = children[0] ? summarizeExpressionAst(children[0], depth + 1) : "hoje";
          const suffix =
            children[0] && children[0].kind === "identifier" && children[0].value === "today"
              ? ""
              : ` de ${base}`;
          if (amount < 0) return `${abs} ${abs === 1 ? singular : plural} atrás${suffix}`;
          if (amount > 0) return `${abs} ${abs === 1 ? singular : plural} à frente${suffix}`;
          return base;
        }
      }
      if (name === "Date.StartOfMonth") return `Início do mês de ${sub(0)}`;
      if (name === "Date.EndOfMonth") return `Fim do mês de ${sub(0)}`;
      if (name === "Date.StartOfYear") return `Início do ano de ${sub(0)}`;
      if (name === "Date.EndOfYear") return `Fim do ano de ${sub(0)}`;
      if (friendly) {
        return children.length
          ? `${friendly} (${children.map((_, i) => sub(i)).join(", ")})`
          : friendly;
      }
      return expressionCanonicalText(node);
    }
    case "binary":
      return `${sub(0)} ${BINARY_OP_TEXT[String(node.value ?? "")] ?? String(node.value ?? "?")} ${sub(1)}`;
    case "unary":
      return `${UNARY_OP_TEXT[String(node.value ?? "")] ?? String(node.value ?? "")} ${sub(0)}`.trim();
    case "if":
      return `Se ${sub(0)}, então ${sub(1)}, senão ${sub(2)}`;
    case "list":
      return children.length
        ? `Lista com ${children.length} ${children.length === 1 ? "item" : "itens"}`
        : "Lista vazia";
    default:
      return expressionCanonicalText(node);
  }
}

/** Resumo a partir do ExpressionSpec persistido (ou null se inválido). */
export function summarizeExpressionSpec(spec: ParamExpressionSpec | null): string {
  const ast = readExpressionAst(spec);
  return summarizeExpressionAst(ast);
}

export type ExpressionNodeGroup = "basic" | "advanced";

/** Taxonomia de produto — kinds canônicos agrupados (§25). */
export const EXPRESSION_NODE_GROUPS: ReadonlyArray<{
  group: ExpressionNodeGroup;
  kind: ParamExpressionNodeKind;
  label: string;
}> = [
  { group: "basic", kind: "call", label: "Função" },
  { group: "basic", kind: "literal", label: "Valor" },
  { group: "basic", kind: "identifier", label: "Referência" },
  { group: "advanced", kind: "binary", label: "Operação" },
  { group: "advanced", kind: "unary", label: "Operação com sinal" },
  { group: "advanced", kind: "if", label: "Condição" },
  { group: "advanced", kind: "list", label: "Lista" },
];

export function expressionNodeKindLabel(kind: ParamExpressionNodeKind): string {
  return EXPRESSION_NODE_GROUPS.find((entry) => entry.kind === kind)?.label ?? kind;
}

/** Rótulo curto de um nó — para linhas compactas de Condição/Lista. */
export function expressionNodeSummary(node: ParamExpressionAst | null): string {
  if (!node) return "Vazio";
  if (node.kind === "identifier" && node.value === "today") return "Hoje";
  if (node.kind === "identifier" && node.value === "now") return "Agora";
  if (node.kind === "literal") return literalFriendlyText(node.value);
  if (node.kind === "call") {
    return FRIENDLY_FUNCTION_LABELS[String(node.value ?? "")] ?? String(node.value ?? "Função");
  }
  return summarizeExpressionAst(node, SUMMARY_MAX_DEPTH - 2);
}

export type ExpressionQuickTemplate = {
  id: string;
  label: string;
  /** Nomes canônicos exigidos no catálogo para o template aparecer. */
  requiredFunctions: string[];
  build: () => ParamExpressionAst;
};

const TODAY: ParamExpressionAst = { kind: "identifier", value: "today" };

/** Starters de UI — montam AST canônico; nunca persistem nome de template. */
export const EXPRESSION_QUICK_TEMPLATES: ReadonlyArray<ExpressionQuickTemplate> = [
  {
    id: "today",
    label: "Hoje",
    requiredFunctions: [],
    build: () => ({ ...TODAY }),
  },
  {
    id: "start-of-month",
    label: "Início do mês atual",
    requiredFunctions: ["Date.StartOfMonth"],
    build: () => ({ kind: "call", value: "Date.StartOfMonth", children: [{ ...TODAY }] }),
  },
  {
    id: "end-of-month",
    label: "Fim do mês atual",
    requiredFunctions: ["Date.EndOfMonth"],
    build: () => ({ kind: "call", value: "Date.EndOfMonth", children: [{ ...TODAY }] }),
  },
  {
    id: "twelve-months-ago",
    label: "12 meses atrás",
    requiredFunctions: ["Date.AddMonths"],
    build: () => ({
      kind: "call",
      value: "Date.AddMonths",
      children: [{ ...TODAY }, { kind: "literal", value: -12 }],
    }),
  },
  {
    id: "same-month-previous-year",
    label: "Mesmo mês do ano passado",
    requiredFunctions: ["Date.StartOfMonth", "Date.AddMonths"],
    build: () => ({
      kind: "call",
      value: "Date.StartOfMonth",
      children: [
        {
          kind: "call",
          value: "Date.AddMonths",
          children: [{ ...TODAY }, { kind: "literal", value: -12 }],
        },
      ],
    }),
  },
];

/**
 * Templates aplicáveis: tipo esperado `date` (ou indeterminado) e todas as
 * funções exigidas presentes no catálogo vivo.
 */
export function availableExpressionTemplates(options: {
  expectedReturnTypes?: ReadonlySet<string> | null;
  functionNames: ReadonlySet<string>;
}): ExpressionQuickTemplate[] {
  const { expectedReturnTypes, functionNames } = options;
  const dateLike = !expectedReturnTypes || expectedReturnTypes.has("date");
  if (!dateLike) return [];
  return EXPRESSION_QUICK_TEMPLATES.filter((template) =>
    template.requiredFunctions.every((name) => functionNames.has(name)),
  );
}

/** Operadores binários expostos no editor — reexport p/ seletor agrupado. */
export { EXPRESSION_BINARY_OPERATORS };
