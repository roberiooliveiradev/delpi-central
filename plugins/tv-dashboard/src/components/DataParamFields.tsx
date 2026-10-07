import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  EXCLUDE_WEEKENDS_PARAM,
  isEffectiveDailyGranularity,
  type ComunicadoDataResolved,
  type ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";
import { useState, type ReactNode } from "react";
import type { BranchScope } from "../api/tvDashboardApi";
import {
  buildDateRangePresetUpdates,
  buildParamValueUpdates,
  type DataParamUpdateValue,
} from "../utils/applyDataParamUpdates";
import {
  resolveParamFieldHint,
  resolveParamFieldLabel,
} from "../content/dataParamCatalog";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  DATE_RANGE_PRESET_OPTIONS,
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
  isDateParam,
  isDateRangePairKey,
  type DateRangePresetId,
} from "../utils/dateRangePresets";
import {
  resolveParamSelectOptions,
  withExcludeWeekendsSchemaField,
  type DataParamSchema,
  type DataParamSchemaField,
} from "../utils/dataParamSchema";
import {
  buildFilterSelectOptions,
  canClearFilterValue,
  normalizeFilterSelectChange,
  resolveBranchEmptyLabel,
  resolveFilterClearLabel,
  resolveFilterLayer,
  resolveFilterSelectValue,
  resolveFilterTextPlaceholder,
  type DataParamFilterLayer,
} from "../utils/dataParamFilterUi";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import {
  buildExpressionParamValue,
  isParamExpressionValue,
  paramAllowsExpression,
  paramFormatToReturnTypes,
  paramTypeToReturnTypes,
} from "../utils/paramExpressions";
import type { ExpressionEditRequest } from "./comunicadoEditorContextCore";
import { BranchField } from "./BranchField";
import { DeckField } from "./deck/DeckField";
import { ExpressionSummaryCard } from "./ExpressionSummaryCard";
import { ConfirmModal } from "./ui/ConfirmModal";

/**
 * Pedido de edição emitido por um campo de param — o host adiciona
 * `previewBlockId` e entrega ao contexto (`openExpressionEditor`).
 */
export type DataParamExpressionEditRequest = Omit<
  ExpressionEditRequest,
  "previewBlockId"
>;

export type { DataParamSchema, DataParamSchemaField } from "../utils/dataParamSchema";

const BRANCH_PARAM_KEYS = new Set(["branch", "filial", "branch_code", "filial_id"]);

function hintForParam(key: string, field: DataParamSchemaField): string | undefined {
  return resolveParamFieldHint(key, field.description);
}

function displayParamValue(
  current: string | number | boolean | ParamExpressionSpec | undefined | null,
  field: DataParamSchemaField,
  applySchemaDefault: boolean,
): string {
  if (isParamExpressionValue(current)) return "";
  if (current === undefined || current === null || current === "") {
    // Camada agregada / limpar: vazio = sem filtro — não preencher com default OpenAPI.
    if (
      applySchemaDefault &&
      field.default !== undefined &&
      field.default !== null
    ) {
      return String(field.default);
    }
    return "";
  }
  return String(current);
}

type Props = {
  schema: DataParamSchema;
  values:
    | Record<
        string,
        string | number | boolean | null | ParamExpressionSpec | undefined
      >
    | undefined;
  inheritedKeys?: Set<string>;
  /** Chaves com valores divergentes entre fontes (multi-seleção). */
  divergedKeys?: Set<string>;
  branchScope?: BranchScope | null;
  idPrefix?: string;
  /** ribbon = grade multi-coluna; pane = empilhado. */
  layout?: "ribbon" | "pane";
  /**
   * Rota com intervalo aberto (ex.: série TRANSFORMA+): Personalizado sem datas =
   * histórico completo.
   */
  openEndedDateRange?: boolean;
  /**
   * Camada canônica dos filtros. `multi` = Não definido aqui + sentinel «Valores diferentes».
   * `aggregate` / `source` = Não definido aqui (opção vazia padronizada).
   */
  filterLayer?: DataParamFilterLayer;
  /**
   * @deprecated Preferir `filterLayer`. false ⇒ aggregate; true ⇒ source.
   */
  hydrateDefaultPreset?: boolean;
  /**
   * Capability de expressões tipadas (catálogo `/data/m/functions`).
   * Ausente/desabilitado → só edição literal/preset (graceful).
   */
  expressionSupport?: ParamExpressionSupport;
  /** fixedQueryParams da rota — nunca editáveis por expressão. */
  fixedQueryParams?: Record<string, unknown> | null;
  /**
   * Recorte de params a renderizar (ex.: flyout «Período» da ribbon só
   * com o grupo de datas). `undefined` = todos.
   */
  onlyParams?: ReadonlySet<string>;
  /** Params a ocultar (ex.: flyout «Filtros» sem o grupo de período). */
  excludeParams?: ReadonlySet<string>;
  /**
   * Params que podem oferecer o modo Expressão (ex.: Filtro só no `paramKey`
   * dono; campos auxiliares seguem literais). `undefined` = todos elegíveis.
   */
  expressionKeys?: ReadonlySet<string>;
  /**
   * Abre o modal de expressão — chamado por «Editar expressão» no
   * cartão-resumo. Ausente → cartão sem ação (somente leitura).
   */
  onEditExpression?: (request: DataParamExpressionEditRequest) => void;
  /** `resolved` do alvo — alimenta resultado/trace do cartão de expressão. */
  resolved?: ComunicadoDataResolved | null;
  /**
   * Patch atômico de parâmetros. Sempre em lote — evita race quando Período +
   * competence / datas mudam juntos (binding stale sobrescrevia o preset).
   * Valores podem ser string (parse via schema) ou ExpressionSpec intacto.
   * (assinatura de método — hosts sem expressionSupport nunca recebem specs)
   */
  onChange(updates: Record<string, DataParamUpdateValue>): void;
};

function ClearableControl({
  clearLabel,
  canClear,
  onClear,
  children,
}: {
  clearLabel: string;
  canClear: boolean;
  onClear: () => void;
  children: ReactNode;
}) {
  return (
    <div className="td-data-param-clearable">
      {children}
      {canClear ? (
        <button
          type="button"
          className="td-data-param-clearable__btn"
          aria-label={clearLabel}
          title={clearLabel}
          onClick={onClear}
        >
          ×
        </button>
      ) : null}
    </div>
  );
}

/**
 * Chips «Valor fixo | Expressão» na linha do label (`labelAside`). Trocar
 * de modo com valor armazenado abre `ConfirmModal` — Cancelar preserva o
 * valor/expressão intactos, Confirmar aplica a troca via patchParam.
 */
function ParamValueModeSwitch({
  mode,
  hasStoredValue,
  idPrefix,
  onSwitch,
}: {
  mode: "literal" | "expression";
  hasStoredValue: boolean;
  idPrefix: string;
  onSwitch: (mode: "literal" | "expression") => void;
}) {
  const [pending, setPending] = useState<"literal" | "expression" | null>(null);

  const request = (next: "literal" | "expression") => {
    if (next === mode) return;
    if (hasStoredValue) setPending(next);
    else onSwitch(next);
  };
  const confirm = () => {
    if (pending) onSwitch(pending);
    setPending(null);
  };

  const btnClass = (active: boolean) =>
    `td-data-param-mode__btn${active ? " td-data-param-mode__btn--active" : ""}`;

  return (
    <div
      className="td-data-param-mode"
      role="group"
      aria-label="Modo do valor"
      id={idPrefix}
    >
      <button
        type="button"
        className={btnClass(mode === "literal")}
        aria-pressed={mode === "literal"}
        onClick={() => request("literal")}
      >
        Valor fixo
      </button>
      <button
        type="button"
        className={btnClass(mode === "expression")}
        aria-pressed={mode === "expression"}
        onClick={() => request("expression")}
      >
        Expressão
      </button>
      <ConfirmModal
        open={pending != null}
        title={
          pending === "expression"
            ? "Trocar para expressão?"
            : "Voltar para valor fixo?"
        }
        message={
          pending === "expression"
            ? "O valor atual será substituído por uma expressão tipada — você poderá editar a fórmula no editor de expressão."
            : "A expressão será descartada e o parâmetro voltará a usar um valor fixo."
        }
        confirmLabel={
          pending === "expression" ? "Trocar para expressão" : "Usar valor fixo"
        }
        onConfirm={confirm}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}

function orderedParamEntries(schema: DataParamSchema): Array<[string, DataParamSchemaField]> {
  const entries = Object.entries(schema);
  const weekendIdx = entries.findIndex(([key]) => key === EXCLUDE_WEEKENDS_PARAM);
  const granIdx = entries.findIndex(([key]) => key === "granularity");
  if (weekendIdx < 0 || granIdx < 0 || weekendIdx === granIdx + 1) return entries;
  const [weekend] = entries.splice(weekendIdx, 1);
  const granAfterMove = entries.findIndex(([key]) => key === "granularity");
  entries.splice(granAfterMove + 1, 0, weekend!);
  return entries;
}

export function DataParamFields({
  schema,
  values,
  inheritedKeys = new Set(),
  divergedKeys = new Set(),
  branchScope = null,
  idPrefix = "td-data-param",
  layout = "pane",
  openEndedDateRange = false,
  filterLayer: filterLayerProp,
  hydrateDefaultPreset = true,
  expressionSupport,
  fixedQueryParams = null,
  onlyParams,
  excludeParams,
  expressionKeys,
  onEditExpression,
  resolved = null,
  onChange,
}: Props) {
  const schemaForUi = withExcludeWeekendsSchemaField(schema);
  const allEntries = orderedParamEntries(schemaForUi);
  const paramVisible = (key: string) =>
    (onlyParams == null || onlyParams.has(key)) &&
    !(excludeParams != null && excludeParams.has(key));
  const entries = allEntries.filter(([key]) => paramVisible(key));
  const fixedQueryParamKeys = new Set(Object.keys(fixedQueryParams ?? {}));
  // Refs `param.<key>` disponíveis — schema completo, mesmo em recorte de flyout.
  const refParamKeys = allEntries.map(([refKey, refField]) => ({
    key: refKey,
    label: resolveParamFieldLabel(refKey, refField.label),
  }));

  const filterLayer = resolveFilterLayer(filterLayerProp, hydrateDefaultPreset);
  const aggregateLayer = filterLayer === "aggregate";
  const uiLabels = {
    clear: TV_DASHBOARD_HELP_TOOLTIPS.data.filterClear,
    unset: TV_DASHBOARD_HELP_TOOLTIPS.data.filterUnsetHere,
    diverged: TV_DASHBOARD_HELP_TOOLTIPS.data.filterValuesDiffer,
    allBranches: TV_DASHBOARD_HELP_TOOLTIPS.data.filterAllBranches,
  };
  const clearLabel = resolveFilterClearLabel(filterLayer, uiLabels);

  /** Opção vazia em selects — limpar / não definido (nunca «Valores diferentes»). */
  function emptyChoiceLabel(inherited: boolean): string {
    return resolveFilterClearLabel(filterLayer, uiLabels, { inherited });
  }

  function emptyTextPlaceholder(
    key: string,
    inherited: boolean,
    field: DataParamSchemaField,
  ): string {
    return resolveFilterTextPlaceholder(
      {
        diverged: divergedKeys.has(key),
        aggregateLayer,
        inherited,
        fieldDefault: field.default,
      },
      uiLabels,
    );
  }

  function commitSelectChange(raw: string, patch: (value: string) => void) {
    const next = normalizeFilterSelectChange(raw);
    if (next === null) return;
    patch(next);
  }

  const compact = layout === "ribbon";
  const selectClass = compact ? "delpi-ui-select--compact" : undefined;
  const nativeClass = compact ? "delpi-ui-native-control--compact" : undefined;
  const datePair = findDateRangeKeys(Object.keys(schemaForUi));
  // SI / IGD também expõem start_date/end_date — o preset relativo (este mês até hoje,
  // semana, ano…) é o mesmo das demais rotas. `competence` permanece opcional para mês fechado.
  const activeDatePair = datePair;
  const presetRaw = String(values?.[DATE_RANGE_PRESET_PARAM] ?? "").trim();
  const preset = (presetRaw || "") as DateRangePresetId | "";
  const isCustom = !activeDatePair || !preset || preset === "custom";
  const showLastN = Boolean(activeDatePair) && preset === "last_n_days";
  const periodDiverged = divergedKeys.has(DATE_RANGE_PRESET_PARAM);
  const periodSelectValue = resolveFilterSelectValue(presetRaw, periodDiverged);
  const periodEmptyLabel = emptyChoiceLabel(false);
  const periodOptions = buildFilterSelectOptions(DATE_RANGE_PRESET_OPTIONS, {
    clearLabel: periodEmptyLabel,
    diverged: periodDiverged,
    divergedLabel: uiLabels.diverged,
  });

  function patchParam(key: string, value: DataParamUpdateValue) {
    // Regra de conflito preset/expressão/competence centralizada no builder
    // compartilhado — modal de expressão usa o mesmo caminho.
    onChange(
      buildParamValueUpdates(key, value, { schema: schemaForUi, values }),
    );
  }

  function patchDateRangePreset(value: string) {
    onChange(
      buildDateRangePresetUpdates(value, { schema: schemaForUi, values }),
    );
  }

  // Grupo «Período» respeita o recorte only/exclude do flyout.
  const rangeGroupKeys = activeDatePair
    ? new Set([
        DATE_RANGE_PRESET_PARAM,
        PERIOD_DAYS_PARAM,
        activeDatePair.startKey,
        activeDatePair.endKey,
      ])
    : null;
  const showRangeFields =
    rangeGroupKeys != null &&
    [...rangeGroupKeys].some((key) => paramVisible(key));

  // Recorte de flyout pode esvaziar os dois blocos — não renderiza nada.
  if (entries.length === 0 && !showRangeFields) return null;

  const rangeFields = !showRangeFields
      ? null
      : [
          <DeckField
            key={DATE_RANGE_PRESET_PARAM}
            id={`${idPrefix}-date-range-preset`}
            label="Período"
            hint={
              openEndedDateRange
                ? TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangePresetOpenEnded
                : !presetRaw && !periodDiverged
                  ? TV_DASHBOARD_HELP_TOOLTIPS.data.filterPeriodRequired
                  : TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangePreset
            }
          >
            <FormSelectControl
              id={`${idPrefix}-date-range-preset`}
              className={selectClass}
              portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
              ariaLabel="Período relativo"
              value={periodSelectValue}
              onChange={(value: string) =>
                commitSelectChange(value, patchDateRangePreset)
              }
              options={periodOptions}
            />
          </DeckField>,
          showLastN ? (
            <DeckField
              key={PERIOD_DAYS_PARAM}
              id={`${idPrefix}-period-days`}
              label="Últimos N dias"
              hint={TV_DASHBOARD_HELP_TOOLTIPS.data.lastNDays}
            >
              <ClearableControl
                clearLabel={clearLabel}
                canClear={canClearFilterValue({
                  diverged: divergedKeys.has(PERIOD_DAYS_PARAM),
                  hasStoredValue:
                    values?.[PERIOD_DAYS_PARAM] !== undefined &&
                    values?.[PERIOD_DAYS_PARAM] !== null &&
                    String(values[PERIOD_DAYS_PARAM]) !== "",
                })}
                onClear={() => onChange({ [PERIOD_DAYS_PARAM]: "" })}
              >
                <NativeTextControl
                  id={`${idPrefix}-period-days`}
                  type="number"
                  className={nativeClass}
                  min={1}
                  max={366}
                  placeholder="Ex.: 15"
                  value={
                    values?.[PERIOD_DAYS_PARAM] === undefined ||
                    values?.[PERIOD_DAYS_PARAM] === null
                      ? ""
                      : String(values[PERIOD_DAYS_PARAM])
                  }
                  onChange={(value: string) => onChange({ [PERIOD_DAYS_PARAM]: value })}
                />
              </ClearableControl>
            </DeckField>
          ) : null,
        ];

  const fields = entries.map(([key, field]) => {
    // periodDays só no bloco de preset (Últimos N dias) quando há par de datas.
    if (activeDatePair && key === PERIOD_DAYS_PARAM) return null;
    if (
      key === EXCLUDE_WEEKENDS_PARAM &&
      !isEffectiveDailyGranularity(schemaForUi, values)
    ) {
      return null;
    }

    const inherited = inheritedKeys.has(key);
    const current = values?.[key];
    const labelBase = resolveParamFieldLabel(key, field.label);
    const label = `${labelBase}${inherited ? " (herdado do slide)" : ""}`;
    const isRangeDate = isDateRangePairKey(key, activeDatePair);
    const hint = isRangeDate
      ? openEndedDateRange
        ? TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangeFixedOpenEnded
        : TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangeFixed
      : key === EXCLUDE_WEEKENDS_PARAM
        ? TV_DASHBOARD_HELP_TOOLTIPS.data.excludeWeekends
        : hintForParam(key, field);
    const fieldId = `${idPrefix}-${key}`;
    const selectOptions = resolveParamSelectOptions(key, field);
    // Nunca aplicar default OpenAPI na exibição — limpar deve mostrar vazio.
    const displayValue = displayParamValue(current, field, false);
    const dateInputsLocked = isRangeDate && !isCustom;
    const emptyLabel = emptyChoiceLabel(inherited);
    const fieldDiverged = divergedKeys.has(key);
    const hasStoredValue =
      current !== undefined &&
      current !== null &&
      (isParamExpressionValue(current) || String(current).trim() !== "");

    // Typed expressions — capability do catálogo + predicate da rota
    // (paramSchema + in:path + expressionAllowed + fixedQueryParams).
    const expressionSpec = isParamExpressionValue(current) ? current : null;
    const exprAllowed =
      Boolean(expressionSupport?.enabled) &&
      (expressionKeys == null || expressionKeys.has(key)) &&
      paramAllowsExpression(key, field, fixedQueryParamKeys);
    const expectedReturnTypes = isDateParam(key, field)
      ? new Set(["date"])
      : (paramFormatToReturnTypes(field.format) ??
        paramTypeToReturnTypes(field.type));

    const modeSwitchAside = exprAllowed ? (
      <ParamValueModeSwitch
        mode={expressionSpec ? "expression" : "literal"}
        hasStoredValue={hasStoredValue}
        idPrefix={`${fieldId}-mode`}
        onSwitch={(mode) => {
          if (mode === "expression") {
            const spec = buildExpressionParamValue(
              isDateParam(key, field)
                ? { kind: "identifier", value: "today" }
                : { kind: "literal" },
            );
            patchParam(key, spec);
            // Troca já entra no authoring — drawer abre com o draft inicial.
            onEditExpression?.({
              paramKey: key,
              paramLabel: labelBase,
              spec,
              expectedReturnTypes,
              refParamKeys: refParamKeys.filter((ref) => ref.key !== key),
              apply: (next) => patchParam(key, next),
            });
          } else {
            patchParam(key, "");
          }
        }}
      />
    ) : null;

    /**
     * Expressão ativa → cartão-resumo («Editar expressão» abre o modal).
     * Literal → controle original com o switch na linha do label.
     * O AST completo é editado só no drawer — aqui não há editor inline.
     */
    const withExpressionMode = (renderLiteral: (labelAside: ReactNode) => ReactNode) => {
      if (!exprAllowed) return renderLiteral(null);
      if (!expressionSpec) return renderLiteral(modeSwitchAside);
      return (
        <DeckField
          key={key}
          id={fieldId}
          label={label}
          labelAside={modeSwitchAside}
          hint={`${hint ? `${hint} ` : ""}${TV_DASHBOARD_HELP_TOOLTIPS.data.paramExpression}`}
        >
          <ClearableControl
            clearLabel={clearLabel}
            canClear={canClearFilterValue({
              diverged: fieldDiverged,
              hasStoredValue,
            })}
            onClear={() => patchParam(key, "")}
          >
            <ExpressionSummaryCard
              spec={expressionSpec}
              paramKey={key}
              resolved={resolved}
              resolvedParamValue={resolved?.effectiveParams?.[key]}
              onEdit={
                onEditExpression
                  ? () =>
                      onEditExpression({
                        paramKey: key,
                        paramLabel: labelBase,
                        spec: expressionSpec,
                        expectedReturnTypes,
                        refParamKeys: refParamKeys.filter((ref) => ref.key !== key),
                        apply: (spec) => patchParam(key, spec),
                      })
                  : undefined
              }
            />
          </ClearableControl>
        </DeckField>
      );
    };

    // Expressão persistida sem capability (catálogo indisponível ou param
    // fora do contrato) — preservar intacta, sem destruir em "[object Object]".
    if (expressionSpec && !exprAllowed) {
      return (
        <DeckField key={key} id={fieldId} label={label} hint={hint}>
          <div className="td-param-expression td-param-expression--readonly">
            <p className="td-param-expression__hint" role="status">
              Expressão tipada persistida — edição indisponível nesta tela.
            </p>
            <ClearableControl
              clearLabel={clearLabel}
              canClear={canClearFilterValue({
                diverged: fieldDiverged,
                hasStoredValue,
              })}
              onClear={() => patchParam(key, "")}
            >
              <pre className="td-param-expression__json">
                {JSON.stringify(expressionSpec.expression.expression, null, 2)}
              </pre>
            </ClearableControl>
          </div>
        </DeckField>
      );
    }

    if (BRANCH_PARAM_KEYS.has(key)) {
      const fieldOptional = field.optional !== false;
      const allowConsolidated =
        fieldOptional && (branchScope == null || branchScope.allowConsolidated !== false);
      const branchEmptyLabel = resolveBranchEmptyLabel(filterLayer, {
        allowConsolidated,
        inherited,
        labels: uiLabels,
      });
      return withExpressionMode((labelAside) => (
        <BranchField
          key={key}
          id={fieldId}
          label={label}
          hint={hint}
          labelAside={labelAside}
          scope={branchScope}
          schemaEnum={field.enum}
          value={displayValue}
          diverged={fieldDiverged}
          onChange={(value) => patchParam(key, value)}
          placeholder={
            fieldDiverged
              ? uiLabels.diverged
              : emptyTextPlaceholder(key, inherited, field)
          }
          emptyOptionLabel={branchEmptyLabel}
          divergedLabel={uiLabels.diverged}
        />
      ));
    }

    if (selectOptions) {
      const options = buildFilterSelectOptions(selectOptions, {
        clearLabel: emptyLabel,
        diverged: fieldDiverged,
        divergedLabel: uiLabels.diverged,
      });
      return withExpressionMode((labelAside) => (
        <DeckField key={key} id={fieldId} label={label} hint={hint} labelAside={labelAside}>
          <FormSelectControl
            id={fieldId}
            className={selectClass}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel={labelBase}
            value={resolveFilterSelectValue(displayValue, fieldDiverged)}
            onChange={(value: string) =>
              commitSelectChange(value, (next) => patchParam(key, next))
            }
            options={options}
          />
        </DeckField>
      ));
    }

    const inputType = isDateParam(key, field)
      ? "date"
      : field.type === "integer" || field.type === "number"
        ? "number"
        : "text";

    const openEndedDatePlaceholder =
      openEndedDateRange && isRangeDate && isCustom
        ? key === activeDatePair?.startKey
          ? "Vazio = início do histórico"
          : "Vazio = até hoje"
        : null;

    return withExpressionMode((labelAside) => (
      <DeckField key={key} id={fieldId} label={label} hint={hint} labelAside={labelAside}>
        <ClearableControl
          clearLabel={clearLabel}
          canClear={canClearFilterValue({
            diverged: fieldDiverged,
            hasStoredValue,
            locked: dateInputsLocked,
          })}
          onClear={() => patchParam(key, "")}
        >
          <NativeTextControl
            id={fieldId}
            type={inputType}
            className={nativeClass}
            disabled={dateInputsLocked}
            placeholder={
              dateInputsLocked
                ? "Definido pelo período relativo"
                : openEndedDatePlaceholder && !aggregateLayer
                  ? openEndedDatePlaceholder
                  : emptyTextPlaceholder(key, inherited, field)
            }
            value={
              dateInputsLocked
                ? ""
                : current === undefined || current === null
                  ? ""
                  : String(current)
            }
            onChange={(value: string) => patchParam(key, value)}
          />
        </ClearableControl>
      </DeckField>
      ));
  });

  const allFields = [...(rangeFields ?? []), ...fields].filter(Boolean);

  if (layout === "ribbon") {
    return <div className="td-deck-ribbon__field-grid">{allFields}</div>;
  }

  return <>{allFields}</>;
}
