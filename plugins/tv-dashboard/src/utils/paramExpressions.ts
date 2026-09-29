/**
 * Typed param expressions — UI authoring helpers (ExpressionSpec v1).
 *
 * O frontend edita a ESTRUTURA do AST apenas — nunca avalia. O contrato
 * canônico é do backend (`value_expression_service`): este módulo espelha
 * apenas o vocabulário estrutural PARAMETER-phase (kinds/operadores/refs)
 * que o wire exige; funções vêm do catálogo (`/data/m/functions`).
 */

import type {
  ParamExpressionAst,
  ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

/** Marker wire — `params[name] = {expression: {version, expression}}`. */
export function isParamExpressionValue(
  value: unknown,
): value is ParamExpressionSpec {
  if (value == null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const inner = (value as Record<string, unknown>).expression;
  return inner != null && typeof inner === "object" && !Array.isArray(inner);
}

/** Lê o AST raiz de um ExpressionSpec; null se a forma não for canônica. */
export function readExpressionAst(
  value: unknown,
): ParamExpressionAst | null {
  if (!isParamExpressionValue(value)) return null;
  const inner = value.expression as Record<string, unknown>;
  const ast = inner.expression;
  if (ast == null || typeof ast !== "object" || Array.isArray(ast)) return null;
  return ast as ParamExpressionAst;
}

/** Empacota um AST no ExpressionSpec v1 canônico. */
export function buildExpressionParamValue(
  ast: ParamExpressionAst,
): ParamExpressionSpec {
  return { expression: { version: 1, expression: ast } };
}

/**
 * Vocabulário estrutural PARAMETER-phase — espelha `_PARAMETER_KINDS` do
 * backend. DERIVED-only kinds (field/record/recordField/each/type) nunca
 * são expostos aqui.
 */
export const PARAMETER_EXPRESSION_NODE_KINDS = [
  "literal",
  "identifier",
  "call",
  "binary",
  "unary",
  "if",
  "list",
] as const;

export type ParamExpressionNodeKind =
  (typeof PARAMETER_EXPRESSION_NODE_KINDS)[number];

/** Operadores binários canônicos (M evaluator). */
export const EXPRESSION_BINARY_OPERATORS = [
  "&",
  "*",
  "+",
  "-",
  "/",
  "<",
  "<=",
  "<>",
  "=",
  ">",
  ">=",
  "and",
  "or",
] as const;

/** Operadores unários canônicos. */
export const EXPRESSION_UNARY_OPERATORS = ["+", "-", "not"] as const;

/** Context refs canônicas — `context:today` / `context:now` no catálogo. */
export const EXPRESSION_CONTEXT_REFERENCES = [
  { id: "today", label: "Hoje" },
  { id: "now", label: "Agora" },
] as const;

export const PARAM_REF_PREFIX = "param.";

/**
 * Predicado `expressionAllowed` por parâmetro — mesma regra do backend
 * (`param_allows_expression`): precisa estar no paramSchema, não pode ser
 * `in: path`, `expressionAllowed: false` nem fixedQueryParam.
 */
export function paramAllowsExpression(
  key: string,
  field: { in?: string; expressionAllowed?: boolean } | undefined,
  fixedQueryKeys?: ReadonlySet<string>,
): boolean {
  if (!field) return false;
  if (String(field.in ?? "").toLowerCase() === "path") return false;
  if (field.expressionAllowed === false) return false;
  if (fixedQueryKeys?.has(key)) return false;
  return true;
}

/** Profundidade do AST (nós internos aninhados). */
export function expressionAstDepth(node: ParamExpressionAst | null): number {
  if (!node) return 0;
  const children = Array.isArray(node.children) ? node.children : [];
  if (children.length === 0) return 1;
  return 1 + Math.max(...children.map((child) => expressionAstDepth(child)));
}

/** Total de nós do AST. */
export function expressionAstNodeCount(node: ParamExpressionAst | null): number {
  if (!node) return 0;
  const children = Array.isArray(node.children) ? node.children : [];
  return (
    1 +
    children.reduce((sum, child) => sum + expressionAstNodeCount(child), 0)
  );
}

/**
 * Nó suportado pelo editor estruturado? Kinds fora do vocabulário ou
 * referências desconhecidas entram como "unsupported" (read-only, sem perda).
 */
export function isSupportedExpressionNode(node: ParamExpressionAst): boolean {
  return PARAMETER_EXPRESSION_NODE_KINDS.includes(
    node.kind as ParamExpressionNodeKind,
  );
}

/**
 * Completude estrutural local — NÃO é validação semântica (backend decide).
 * Apenas detecta nós incompletos para sinalizar na UI.
 */
export function expressionAstIncomplete(node: ParamExpressionAst | null): boolean {
  if (!node) return true;
  if (!isSupportedExpressionNode(node)) return false;
  const children = Array.isArray(node.children) ? node.children : [];
  switch (node.kind) {
    case "literal":
      return node.value === undefined;
    case "identifier":
      return typeof node.value !== "string" || !String(node.value).trim();
    case "call":
      // Arity mínima é checada pelo editor (conhece o catálogo); 0-arg calls existem.
      return (
        typeof node.value !== "string" ||
        !String(node.value).trim() ||
        children.some(expressionAstIncomplete)
      );
    case "binary":
    case "unary":
      return (
        typeof node.value !== "string" ||
        !String(node.value).trim() ||
        children.length === 0 ||
        children.some(expressionAstIncomplete)
      );
    case "if":
      return children.length < 3 || children.some(expressionAstIncomplete);
    case "list":
      return children.some(expressionAstIncomplete);
    default:
      return true;
  }
}

/** Signature `Name(arg1, optional arg2) as type` → metadados de arity. */
export type ParsedFunctionSignature = {
  /** Nomes dos argumentos na ordem (sem o prefixo "optional"). */
  args: string[];
  /** Índice a partir do qual os args são opcionais (args.length = nenhum). */
  optionalFrom: number;
  /** Tipo de retorno (`as <type>`) ou null. */
  returnType: string | null;
};

export function parseFunctionSignature(
  signature: string | undefined | null,
): ParsedFunctionSignature {
  const sig = String(signature ?? "").trim();
  const open = sig.indexOf("(");
  const close = sig.lastIndexOf(")");
  if (open < 0 || close <= open) {
    return { args: [], optionalFrom: 0, returnType: parseReturnType(sig) };
  }
  const inner = sig.slice(open + 1, close).trim();
  const rawArgs = inner ? inner.split(",").map((part) => part.trim()) : [];
  const args = rawArgs.map((part) => part.replace(/^optional\s+/i, ""));
  const optionalFrom = rawArgs.findIndex((part) => /^optional\s+/i.test(part));
  return {
    args,
    optionalFrom: optionalFrom < 0 ? args.length : optionalFrom,
    returnType: parseReturnType(sig.slice(close + 1)),
  };
}

function parseReturnType(tail: string): string | null {
  const match = /\bas\s+([A-Za-z_][\w ]*)$/.exec(tail.trim());
  return match ? match[1].trim() : null;
}

/** Mapeia tipo do paramSchema → tipo de retorno esperado na signature. */
export function paramTypeToReturnTypes(
  paramType: string | undefined,
): ReadonlySet<string> | null {
  switch (paramType) {
    case "integer":
    case "number":
      return new Set(["number"]);
    case "boolean":
      return new Set(["logical", "boolean"]);
    case "string":
      // format: date aponta data via paramFormat (caller decide).
      return null;
    default:
      return null;
  }
}

/** format: date → retorno esperado date/datetime. */
export function paramFormatToReturnTypes(
  format: string | undefined,
): ReadonlySet<string> | null {
  const normalized = String(format ?? "").toLowerCase();
  if (normalized === "date") return new Set(["date"]);
  if (normalized === "date-time") return new Set(["datetime", "date"]);
  return null;
}

/** Entrada do trace backend (`resolved.paramExpressions`) de um parâmetro. */
export type ParamExpressionTraceEntry = {
  resolved?: unknown;
  error?: { message?: unknown; code?: unknown } | null;
  expectedType?: unknown;
};

/** Lookup do trace por parâmetro no `resolved` enriquecido do backend. */
export function findParamExpressionTrace(
  resolved: unknown,
  paramKey: string,
): ParamExpressionTraceEntry | null {
  if (!resolved || typeof resolved !== "object") return null;
  const raw = (resolved as { paramExpressions?: unknown }).paramExpressions;
  if (!Array.isArray(raw)) return null;
  const entry = raw.find(
    (item) =>
      item &&
      typeof item === "object" &&
      (item as { param?: unknown }).param === paramKey,
  );
  return (entry as ParamExpressionTraceEntry | undefined) ?? null;
}
