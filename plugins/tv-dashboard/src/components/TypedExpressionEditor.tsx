/**
 * TypedExpressionEditor — editor estruturado de ExpressionSpec v1.
 *
 * Edita APENAS a estrutura do AST (kinds/operadores/refs do vocabulário
 * PARAMETER-phase; funções do catálogo vivo `/data/m/functions`).
 * Nunca avalia, nunca infere valor resolvido — o backend é a autoridade.
 */

import { useMemo } from "react";
import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { INPUT_EXPRESSION_REF_PREFIX } from "@delpi/tv-dashboard-presentation";
import type {
  ParamExpressionAst,
  ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

import type { MFunctionCatalogItem } from "../api/tvDashboardApi";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  EXPRESSION_BINARY_OPERATORS,
  EXPRESSION_CONTEXT_REFERENCES,
  EXPRESSION_UNARY_OPERATORS,
  PARAM_REF_PREFIX,
  buildExpressionParamValue,
  expressionAstDepth,
  expressionAstIncomplete,
  expressionAstNodeCount,
  isSupportedExpressionNode,
  parseFunctionSignature,
  readExpressionAst,
  type ParamExpressionNodeKind,
} from "../utils/paramExpressions";
import {
  EXPRESSION_NODE_GROUPS,
  friendlyFunctionLabel,
  friendlyFunctionReturnTypeLabel,
} from "../utils/paramExpressionLabels";

/** Limite de authoring da UI (não é o limite do backend — só guarda estrutural). */
const UI_MAX_AUTHORING_DEPTH = 10;
const UI_MAX_AUTHORING_NODES = 64;

/** Tipos de nó — taxonomia amigável canônica (Básicos primeiro, §25). */
const NODE_KIND_OPTIONS: Array<{ value: ParamExpressionNodeKind; label: string }> =
  EXPRESSION_NODE_GROUPS.map((entry) => ({ value: entry.kind, label: entry.label }));

const BINARY_OPERATOR_LABELS: Record<string, string> = {
  "&": "& (texto)",
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

const UNARY_OPERATOR_LABELS: Record<string, string> = {
  "+": "+ (positivo)",
  "-": "− (negativo)",
  not: "não (not)",
};

function defaultNode(kind: ParamExpressionNodeKind): ParamExpressionAst {
  switch (kind) {
    case "identifier":
      return { kind: "identifier", value: "today" };
    case "call":
      return { kind: "call", value: "" };
    case "binary":
      return {
        kind: "binary",
        value: "+",
        children: [{ kind: "literal" }, { kind: "literal" }],
      };
    case "unary":
      return { kind: "unary", value: "-", children: [{ kind: "literal" }] };
    case "if":
      return {
        kind: "if",
        children: [{ kind: "literal" }, { kind: "literal" }, { kind: "literal" }],
      };
    case "list":
      return { kind: "list", children: [] };
    case "literal":
    default:
      return { kind: "literal" };
  }
}

type FunctionMeta = {
  name: string;
  signature: string;
  description: string;
  argNames: string[];
  requiredArgs: number;
  maxArgs: number;
  returnType: string | null;
};

function functionMeta(item: MFunctionCatalogItem): FunctionMeta {
  const parsed = parseFunctionSignature(item.signature);
  const required = Array.isArray(item.parameters)
    ? item.parameters.length
    : parsed.optionalFrom;
  const maxArgs = Math.max(parsed.args.length, required);
  const argNames = parsed.args.length
    ? parsed.args
    : (item.parameters ?? []).map(String);
  return {
    name: item.name,
    signature: item.signature ?? item.name,
    description: item.description ?? "",
    argNames,
    requiredArgs: Math.min(required, maxArgs),
    maxArgs,
    returnType: parsed.returnType,
  };
}

/** AST contém nó fora do vocabulário do editor? (read-only, sem destruir). */
function hasUnsupportedNode(node: ParamExpressionAst): boolean {
  if (!isSupportedExpressionNode(node)) return true;
  return (node.children ?? []).some(hasUnsupportedNode);
}

export type TypedExpressionEditorProps = {
  /** ExpressionSpec persistido. */
  value: ParamExpressionSpec;
  onChange: (next: ParamExpressionSpec) => void;
  support: ParamExpressionSupport;
  /** Chaves do paramSchema para refs `param.<key>`. */
  refParamKeys?: Array<{ key: string; label: string }>;
  /** Variáveis do slide para refs `input.<key>`. */
  refInputKeys?: Array<{ key: string; label: string }>;
  /** Tipos de retorno compatíveis com o param (ordena funções). */
  expectedReturnTypes?: ReadonlySet<string> | null;
  idPrefix?: string;
  compact?: boolean;
};

export function TypedExpressionEditor({
  value,
  onChange,
  support,
  refParamKeys = [],
  refInputKeys = [],
  expectedReturnTypes = null,
  idPrefix = "td-expr",
  compact = false,
}: TypedExpressionEditorProps) {
  const ast = readExpressionAst(value);
  const metas = useMemo(
    () => support.functions.map(functionMeta),
    [support.functions],
  );

  const emit = (next: ParamExpressionAst) =>
    onChange(buildExpressionParamValue(next));

  if (!ast) {
    return (
      <p className="td-param-expression__hint" role="alert">
        ExpressionSpec inválido — estrutura ausente. Remova a expressão ou
        corrija via backend.
      </p>
    );
  }

  const depth = expressionAstDepth(ast);
  const nodes = expressionAstNodeCount(ast);
  const unsupported = hasUnsupportedNode(ast) || depth > UI_MAX_AUTHORING_DEPTH;

  if (unsupported) {
    return (
      <div className="td-param-expression td-param-expression--readonly">
        <p className="td-param-expression__hint" role="status">
          Expressão não suportada por este editor — preservada sem alteração.
        </p>
        <pre className="td-param-expression__json">
          {JSON.stringify(ast, null, 2)}
        </pre>
      </div>
    );
  }

  const incomplete = expressionAstIncomplete(ast);

  return (
    <div
      className={`td-param-expression${compact ? " td-param-expression--compact" : ""}`}
      data-expression-incomplete={incomplete || undefined}
    >
      <ExpressionNodeEditor
        node={ast}
        onChange={emit}
        depth={1}
        metas={metas}
        refParamKeys={refParamKeys}
        refInputKeys={refInputKeys}
        expectedReturnTypes={expectedReturnTypes}
        idPrefix={idPrefix}
        compact={compact}
      />
      {incomplete ? (
        <p className="td-param-expression__hint" role="status">
          Expressão incompleta — o backend valida a semântica ao salvar/preview.
        </p>
      ) : null}
      {nodes > UI_MAX_AUTHORING_NODES ? (
        <p className="td-param-expression__hint" role="alert">
          Expressão muito grande para edição estrutural ({nodes} nós).
        </p>
      ) : null}
    </div>
  );
}

type NodeEditorProps = {
  node: ParamExpressionAst;
  onChange: (next: ParamExpressionAst) => void;
  depth: number;
  metas: FunctionMeta[];
  refParamKeys: Array<{ key: string; label: string }>;
  refInputKeys: Array<{ key: string; label: string }>;
  expectedReturnTypes: ReadonlySet<string> | null;
  idPrefix: string;
  compact: boolean;
};

function ExpressionNodeEditor(props: NodeEditorProps) {
  const { node, onChange, depth, idPrefix, compact } = props;
  const canNest = depth < UI_MAX_AUTHORING_DEPTH;

  const setChild = (index: number, child: ParamExpressionAst) => {
    const children = [...(node.children ?? [])];
    children[index] = child;
    onChange({ ...node, children });
  };

  const kindSelector = (
    <FormSelectControl
      id={`${idPrefix}-kind-${depth}`}
      className={compact ? "delpi-ui-select--compact" : undefined}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      ariaLabel="Tipo do nó"
      value={node.kind}
      onChange={(next) => {
        if (next !== node.kind) {
          onChange(defaultNode(next as ParamExpressionNodeKind));
        }
      }}
      options={NODE_KIND_OPTIONS.map((option) => ({
        value: option.value,
        label: option.label,
      }))}
    />
  );

  return (
    <div className="td-param-expression__node" data-node-kind={node.kind}>
      <div className="td-param-expression__node-head">{kindSelector}</div>
      <NodeBody
        {...props}
        setChild={setChild}
        renderChild={(index, label) =>
          canNest ? (
            <div className="td-param-expression__child" key={index}>
              <span className="td-param-expression__child-label">{label}</span>
              <ExpressionNodeEditor
                {...props}
                node={node.children?.[index] ?? { kind: "literal" }}
                onChange={(next) => setChild(index, next)}
                depth={depth + 1}
                idPrefix={`${idPrefix}-c${index}`}
              />
            </div>
          ) : (
            <p
              className="td-param-expression__hint"
              role="alert"
              key={index}
            >
              Profundidade máxima do editor atingida.
            </p>
          )
        }
      />
    </div>
  );
}

type NodeBodyProps = NodeEditorProps & {
  setChild: (index: number, child: ParamExpressionAst) => void;
  renderChild: (index: number, label: string) => React.ReactNode;
};

function NodeBody(props: NodeBodyProps) {
  const { node, onChange, metas, refParamKeys, refInputKeys, idPrefix, compact, renderChild } =
    props;
  const selectClass = compact ? "delpi-ui-select--compact" : undefined;
  const nativeClass = compact ? "delpi-ui-native-control--compact" : undefined;

  switch (node.kind) {
    case "literal":
      return (
        <LiteralEditor
          node={node}
          onChange={onChange}
          idPrefix={idPrefix}
          nativeClass={nativeClass}
          selectClass={selectClass}
        />
      );
    case "identifier": {
      const options = [
        ...EXPRESSION_CONTEXT_REFERENCES.map((ref) => ({
          value: ref.id,
          label: ref.label,
        })),
        ...refParamKeys.map((ref) => ({
          value: `${PARAM_REF_PREFIX}${ref.key}`,
          label: `Parâmetro ${ref.label || ref.key}`,
        })),
        ...refInputKeys.map((ref) => ({
          value: `${INPUT_EXPRESSION_REF_PREFIX}${ref.key}`,
          label: `Variável ${ref.label || ref.key}`,
        })),
      ];
      const current = String(node.value ?? "");
      const known = options.some((option) => option.value === current);
      return (
        <FormSelectControl
          id={`${idPrefix}-ref`}
          className={selectClass}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          ariaLabel="Referência"
          value={known ? current : ""}
          onChange={(next) => onChange({ ...node, value: next })}
          options={[
            ...(known
              ? []
              : current
                ? [{ value: current, label: `Ref. ${current}` }]
                : [{ value: "", label: "Selecionar…" }]),
            ...options,
          ]}
        />
      );
    }
    case "call": {
      const current = String(node.value ?? "");
      const meta = metas.find((item) => item.name === current);
      // Type-aware ordering (§16): funções com retorno compatível primeiro —
      // apenas sugestão de ordem, não validação (backend decide a semântica).
      const expected = props.expectedReturnTypes;
      const ordered = expected
        ? [...metas].sort((a, b) => {
            const aOk = a.returnType != null && expected.has(a.returnType) ? 0 : 1;
            const bOk = b.returnType != null && expected.has(b.returnType) ? 0 : 1;
            return aOk - bOk || a.name.localeCompare(b.name);
          })
        : metas;
      const options = ordered.map((item) => {
        const friendly = friendlyFunctionLabel(item.name);
        const typeMark =
          expected && item.returnType != null && expected.has(item.returnType)
            ? ` → ${friendlyFunctionReturnTypeLabel(item.returnType)}`
            : "";
        // Label amigável + nome canônico — a busca continua achando "Date.Add…".
        return {
          value: item.name,
          label:
            friendly === item.name
              ? `${item.name}${typeMark}`
              : `${friendly} (${item.name})${typeMark}`,
        };
      });
      const argCount = node.children?.length ?? 0;
      const canAddArg = meta ? argCount < meta.maxArgs : false;
      return (
        <div className="td-param-expression__call">
          <FormSelectControl
            id={`${idPrefix}-fn`}
            className={selectClass}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel="Função"
            searchable
            value={current}
            onChange={(next) => {
              const meta = metas.find((item) => item.name === next);
              const slots = meta ? meta.requiredArgs : 0;
              onChange({
                kind: "call",
                value: next,
                children: Array.from({ length: slots }, () => ({
                  kind: "literal",
                })),
              });
            }}
            options={[
              { value: "", label: "Selecionar função…" },
              ...options,
            ]}
          />
          {meta?.signature ? (
            <p className="td-param-expression__signature">
              {meta.description ? (
                <span className="td-param-expression__fn-desc">
                  {meta.description}
                </span>
              ) : null}
              <code>{meta.signature}</code>
            </p>
          ) : null}
          {(node.children ?? []).map((_, index) => (
            <span key={index}>
              {renderChild(
                index,
                meta?.argNames[index] ?? `Argumento ${index + 1}`,
              )}
            </span>
          ))}
          {canAddArg ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() =>
                onChange({
                  ...node,
                  children: [...(node.children ?? []), { kind: "literal" }],
                })
              }
            >
              Adicionar argumento
            </button>
          ) : null}
          {meta && argCount > meta.requiredArgs ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              onClick={() =>
                onChange({
                  ...node,
                  children: (node.children ?? []).slice(0, -1),
                })
              }
            >
              Remover argumento
            </button>
          ) : null}
        </div>
      );
    }
    case "binary":
      return (
        <div className="td-param-expression__op">
          <FormSelectControl
            id={`${idPrefix}-op`}
            className={selectClass}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel="Operador"
            value={String(node.value ?? "")}
            onChange={(next) => onChange({ ...node, value: next })}
            options={EXPRESSION_BINARY_OPERATORS.map((op) => ({
              value: op,
              label: BINARY_OPERATOR_LABELS[op] ?? op,
            }))}
          />
          {renderChild(0, "Lado esquerdo")}
          {renderChild(1, "Lado direito")}
        </div>
      );
    case "unary":
      return (
        <div className="td-param-expression__op">
          <FormSelectControl
            id={`${idPrefix}-op`}
            className={selectClass}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel="Operador unário"
            value={String(node.value ?? "")}
            onChange={(next) => onChange({ ...node, value: next })}
            options={EXPRESSION_UNARY_OPERATORS.map((op) => ({
              value: op,
              label: UNARY_OPERATOR_LABELS[op] ?? op,
            }))}
          />
          {renderChild(0, "Valor")}
        </div>
      );
    case "if":
      return (
        <div className="td-param-expression__if">
          {renderChild(0, "Se")}
          {renderChild(1, "Então")}
          {renderChild(2, "Senão")}
        </div>
      );
    case "list": {
      const children = node.children ?? [];
      return (
        <div className="td-param-expression__list">
          {children.map((_, index) => (
            <div key={index} className="td-param-expression__list-item">
              {renderChild(index, `Item ${index + 1}`)}
              <button
                type="button"
                className="td-param-expression__remove"
                aria-label={`Remover item ${index + 1}`}
                onClick={() =>
                  onChange({
                    ...node,
                    children: children.filter((_, i) => i !== index),
                  })
                }
              >
                ×
              </button>
            </div>
          ))}
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() =>
              onChange({
                ...node,
                children: [...children, { kind: "literal" }],
              })
            }
          >
            Adicionar item
          </button>
        </div>
      );
    }
    default:
      return (
        <pre className="td-param-expression__json">
          {JSON.stringify(node, null, 2)}
        </pre>
      );
  }
}

function LiteralEditor({
  node,
  onChange,
  idPrefix,
  nativeClass,
  selectClass,
}: {
  node: ParamExpressionAst;
  onChange: (next: ParamExpressionAst) => void;
  idPrefix: string;
  nativeClass?: string;
  selectClass?: string;
}) {
  const value = node.value;
  const literalType =
    value === null
      ? "null"
      : value === undefined
        ? "unset"
        : typeof value === "boolean"
          ? "boolean"
          : typeof value === "number"
            ? "number"
            : /^\d{4}-\d{2}-\d{2}$/.test(String(value))
              ? "date"
              : "string";

  const setType = (next: string) => {
    if (next === "null") onChange({ kind: "literal", value: null });
    else if (next === "boolean") onChange({ kind: "literal", value: true });
    else if (next === "number") onChange({ kind: "literal", value: 0 });
    else if (next === "date")
      onChange({ kind: "literal", value: "2026-01-01" });
    else onChange({ kind: "literal", value: "" });
  };

  return (
    <div className="td-param-expression__literal">
      <FormSelectControl
        id={`${idPrefix}-lit-type`}
        className={selectClass}
        portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
        ariaLabel="Tipo do literal"
        value={literalType === "unset" ? "string" : literalType}
        onChange={setType}
        options={[
          { value: "string", label: "Texto" },
          { value: "number", label: "Número" },
          { value: "boolean", label: "Booleano" },
          { value: "date", label: "Data" },
          { value: "null", label: "Nulo" },
        ]}
      />
      {literalType === "null" ? null : literalType === "boolean" ? (
        <FormSelectControl
          id={`${idPrefix}-lit-bool`}
          className={selectClass}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          ariaLabel="Valor booleano"
          value={value === true ? "true" : "false"}
          onChange={(next) =>
            onChange({ kind: "literal", value: next === "true" })
          }
          options={[
            { value: "true", label: "Sim" },
            { value: "false", label: "Não" },
          ]}
        />
      ) : (
        <NativeTextControl
          id={`${idPrefix}-lit-value`}
          type={
            literalType === "number"
              ? "number"
              : literalType === "date"
                ? "date"
                : "text"
          }
          className={nativeClass}
          placeholder={
            literalType === "number"
              ? "Ex.: -12"
              : literalType === "date"
                ? "AAAA-MM-DD"
                : "Texto"
          }
          value={value === undefined || value === null ? "" : String(value)}
          onChange={(raw) => {
            if (literalType === "number") {
              const parsed = Number(raw);
              onChange({
                kind: "literal",
                value: raw.trim() === "" || !Number.isFinite(parsed) ? undefined : parsed,
              });
            } else {
              onChange({ kind: "literal", value: raw });
            }
          }}
        />
      )}
    </div>
  );
}
