import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import type { BranchScope } from "../api/tvDashboardApi";
import {
  ENUM_OPTION_LABELS,
  UI_FALLBACK_ENUMS,
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
  isDateRangePairKey,
  type DateRangePresetId,
} from "../utils/dateRangePresets";
import { BranchField } from "./BranchField";
import { DeckField } from "./deck/DeckField";

export type DataParamSchemaField = {
  type?: string;
  label?: string;
  description?: string;
  default?: string | number | boolean;
  optional?: boolean;
  enum?: Array<string | number | boolean>;
};

export type DataParamSchema = Record<string, DataParamSchemaField>;

const BRANCH_PARAM_KEYS = new Set(["branch", "filial", "branch_code", "filial_id"]);

const DATE_PARAM_KEYS = new Set([
  "start_date",
  "end_date",
  "date_start",
  "date_end",
  "dataInicio",
  "dataFim",
  "data_inicial",
  "data_final",
  "reference_date",
  "date",
  "date_from",
  "date_to",
  "data_inicio",
  "data_fim",
  "issue_date_start",
  "issue_date_end",
  "modified_from",
  "modified_to",
  "from",
  "to",
]);

/** Máximo de campos inline na ribbon; acima disso abre modal. */
export const RIBBON_INLINE_PARAM_LIMIT = 4;

function hintForParam(key: string, field: DataParamSchemaField): string | undefined {
  return resolveParamFieldHint(key, field.description);
}

export function enumOptionLabel(paramKey: string, value: string): string {
  return ENUM_OPTION_LABELS[paramKey]?.[value] ?? value;
}

export function resolveParamSelectOptions(
  key: string,
  field: DataParamSchemaField,
): Array<{ value: string; label: string }> | null {
  // Período em dias: sempre input numérico (qualquer valor positivo).
  if (key === PERIOD_DAYS_PARAM) return null;

  const rawEnum = Array.isArray(field.enum)
    ? field.enum.filter((item) => item !== null && item !== undefined)
    : [];
  const values =
    rawEnum.length > 0
      ? rawEnum
      : field.type === "boolean"
        ? [true, false]
        : (UI_FALLBACK_ENUMS[key] ?? null);
  if (!values || values.length === 0) return null;

  if (field.type === "boolean" || values.every((item) => typeof item === "boolean")) {
    return values.map((item) => ({
      value: String(item),
      label: item === true || String(item) === "true" ? "Sim" : "Não",
    }));
  }

  return values.map((item) => {
    const value = String(item);
    return { value, label: enumOptionLabel(key, value) };
  });
}

function isDateParam(key: string, field: DataParamSchemaField): boolean {
  if (DATE_PARAM_KEYS.has(key)) return true;
  const format = String((field as { format?: string }).format || "").toLowerCase();
  return format === "date" || format === "date-time";
}

function displayParamValue(
  current: string | number | boolean | undefined | null,
  field: DataParamSchemaField,
  applySchemaDefault: boolean,
): string {
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
  values: Record<string, string | number | boolean | null | undefined> | undefined;
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
   * Quando false, camada agregada (slide/programação/multi): rótulo vazio =
   * «Não definido (usa a fonte)». Default true na fonte (rótulo «Limpar filtro»).
   */
  hydrateDefaultPreset?: boolean;
  /**
   * Patch atômico de parâmetros. Sempre em lote — evita race quando Período +
   * competence / datas mudam juntos (binding stale sobrescrevia o preset).
   */
  onChange: (updates: Record<string, string>) => void;
};

/** @deprecated Preferir rótulos em helpTooltips; mantido para testes de contrato. */
export function resolveFallbackPreset(openEndedDateRange: boolean): DateRangePresetId {
  return openEndedDateRange ? "custom" : "this_month";
}

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

export function DataParamFields({
  schema,
  values,
  inheritedKeys = new Set(),
  divergedKeys = new Set(),
  branchScope = null,
  idPrefix = "td-data-param",
  layout = "pane",
  openEndedDateRange = false,
  hydrateDefaultPreset = true,
  onChange,
}: Props) {
  const entries = Object.entries(schema);
  if (entries.length === 0) return null;

  const aggregateLayer = !hydrateDefaultPreset;
  const unsetLabel = TV_DASHBOARD_HELP_TOOLTIPS.data.filterUnsetUsesSource;
  const clearLabel = TV_DASHBOARD_HELP_TOOLTIPS.data.filterClear;
  const divergedLabel = TV_DASHBOARD_HELP_TOOLTIPS.data.filterValuesDiffer;

  /** Opção vazia em selects — limpar / não definido / valores diferentes. */
  function emptyChoiceLabel(key: string, inherited: boolean): string {
    if (divergedKeys.has(key)) return divergedLabel;
    if (aggregateLayer) return unsetLabel;
    if (inherited) return "Herdado do slide";
    return clearLabel;
  }

  function emptyTextPlaceholder(
    key: string,
    inherited: boolean,
    field: DataParamSchemaField,
  ): string {
    if (divergedKeys.has(key)) return divergedLabel;
    if (aggregateLayer) return unsetLabel;
    if (inherited) return "Herdado do slide";
    if (field.default !== undefined) return `Padrão: ${field.default}`;
    return clearLabel;
  }

  const compact = layout === "ribbon";
  const selectClass = compact ? "delpi-ui-select--compact" : undefined;
  const nativeClass = compact ? "delpi-ui-native-control--compact" : undefined;
  const datePair = findDateRangeKeys(Object.keys(schema));
  // SI / IGD também expõem start_date/end_date — o preset relativo (este mês até hoje,
  // semana, ano…) é o mesmo das demais rotas. `competence` permanece opcional para mês fechado.
  const hasCompetence = "competence" in schema;
  const activeDatePair = datePair;
  const presetRaw = String(values?.[DATE_RANGE_PRESET_PARAM] ?? "").trim();
  const preset = (presetRaw || "") as DateRangePresetId | "";
  const isCustom = !activeDatePair || !preset || preset === "custom";
  const showLastN = Boolean(activeDatePair) && preset === "last_n_days";
  // Sem preset gravado → opção «Limpar» / «Não definido» (rotas fechadas exigem escolha explícita).
  const periodSelectValue = presetRaw;
  const periodEmptyLabel = divergedKeys.has(DATE_RANGE_PRESET_PARAM)
    ? divergedLabel
    : aggregateLayer
      ? unsetLabel
      : clearLabel;

  function patchParam(key: string, value: string) {
    const updates: Record<string, string> = { [key]: value };
    if (key === "competence" && value.trim() && activeDatePair) {
      // Competência (mês fechado SI) → datas manuais; evita conflito com preset relativo.
      updates[DATE_RANGE_PRESET_PARAM] = "custom";
    }
    if (activeDatePair && isDateRangePairKey(key, activeDatePair) && preset && preset !== "custom") {
      updates[DATE_RANGE_PRESET_PARAM] = "custom";
    }
    onChange(updates);
  }

  function patchDateRangePreset(value: string) {
    const updates: Record<string, string> = { [DATE_RANGE_PRESET_PARAM]: value };
    if (hasCompetence && value && value !== "custom") {
      // Preset relativo (até hoje) vence competência — limpa o mês SI.
      updates.competence = "";
    }
    // Preset relativo / limpar: não reaproveitar datas fixas de outra camada (ex.: 0026).
    if (activeDatePair && value !== "custom") {
      updates[activeDatePair.startKey] = "";
      updates[activeDatePair.endKey] = "";
      if (value !== "last_n_days") {
        updates[PERIOD_DAYS_PARAM] = "";
      }
    }
    onChange(updates);
  }

  const rangeFields =
    activeDatePair == null
      ? null
      : [
          <DeckField
            key={DATE_RANGE_PRESET_PARAM}
            id={`${idPrefix}-date-range-preset`}
            label="Período"
            hint={
              openEndedDateRange
                ? TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangePresetOpenEnded
                : !periodSelectValue
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
              onChange={patchDateRangePreset}
              options={[
                { value: "", label: periodEmptyLabel },
                ...DATE_RANGE_PRESET_OPTIONS,
              ]}
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
                canClear={
                  values?.[PERIOD_DAYS_PARAM] !== undefined &&
                  values?.[PERIOD_DAYS_PARAM] !== null &&
                  String(values[PERIOD_DAYS_PARAM]) !== ""
                }
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

    const inherited = inheritedKeys.has(key);
    const current = values?.[key];
    const labelBase = resolveParamFieldLabel(key, field.label);
    const label = `${labelBase}${inherited ? " (herdado do slide)" : ""}`;
    const isRangeDate = isDateRangePairKey(key, activeDatePair);
    const hint = isRangeDate
      ? openEndedDateRange
        ? TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangeFixedOpenEnded
        : TV_DASHBOARD_HELP_TOOLTIPS.data.dateRangeFixed
      : hintForParam(key, field);
    const fieldId = `${idPrefix}-${key}`;
    const selectOptions = resolveParamSelectOptions(key, field);
    // Nunca aplicar default OpenAPI na exibição — limpar deve mostrar vazio.
    const displayValue = displayParamValue(current, field, false);
    const dateInputsLocked = isRangeDate && !isCustom;
    const emptyLabel = emptyChoiceLabel(key, inherited);
    const hasStoredValue =
      current !== undefined && current !== null && String(current).trim() !== "";

    if (BRANCH_PARAM_KEYS.has(key)) {
      return (
        <BranchField
          key={key}
          id={fieldId}
          label={label}
          hint={hint}
          scope={branchScope}
          schemaEnum={field.enum}
          value={displayValue}
          onChange={(value) => patchParam(key, value)}
          placeholder={emptyTextPlaceholder(key, inherited, field)}
          emptyOptionLabel={emptyLabel}
        />
      );
    }

    if (selectOptions) {
      return (
        <DeckField key={key} id={fieldId} label={label} hint={hint}>
          <FormSelectControl
            id={fieldId}
            className={selectClass}
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel={labelBase}
            value={displayValue}
            onChange={(value: string) => patchParam(key, value)}
            options={[{ value: "", label: emptyLabel }, ...selectOptions]}
          />
        </DeckField>
      );
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

    return (
      <DeckField key={key} id={fieldId} label={label} hint={hint}>
        <ClearableControl
          clearLabel={clearLabel}
          canClear={hasStoredValue && !dateInputsLocked}
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
    );
  });

  const allFields = [...(rangeFields ?? []), ...fields].filter(Boolean);

  if (layout === "ribbon") {
    return <div className="td-deck-ribbon__field-grid">{allFields}</div>;
  }

  return <>{allFields}</>;
}

export function visibleParamSchema(
  schema: DataParamSchema | undefined | null,
  fixedQueryParams?: Record<string, unknown> | null,
): DataParamSchema {
  const base = (schema ?? {}) as DataParamSchema;
  const fixed = fixedQueryParams ?? {};
  if (!fixed || Object.keys(fixed).length === 0) return base;
  return Object.fromEntries(Object.entries(base).filter(([key]) => !(key in fixed)));
}
