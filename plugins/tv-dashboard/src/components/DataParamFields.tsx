import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { BranchScope } from "../api/tvDashboardApi";
import { ENUM_OPTION_LABELS, UI_FALLBACK_ENUMS } from "../content/dataParamCatalog";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
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
  const fromSchema = field.description?.trim();
  if (fromSchema) return fromSchema;
  if (key === "granularity") return TV_DASHBOARD_HELP_TOOLTIPS.data.paramGranularity;
  if (key === "periodDays") return TV_DASHBOARD_HELP_TOOLTIPS.data.paramPeriodDays;
  if (BRANCH_PARAM_KEYS.has(key)) return TV_DASHBOARD_HELP_TOOLTIPS.data.paramBranch;
  if (key === "customer_segment") return TV_DASHBOARD_HELP_TOOLTIPS.data.paramCustomerSegment;
  return undefined;
}

export function enumOptionLabel(paramKey: string, value: string): string {
  return ENUM_OPTION_LABELS[paramKey]?.[value] ?? value;
}

export function resolveParamSelectOptions(
  key: string,
  field: DataParamSchemaField,
): Array<{ value: string; label: string }> | null {
  // Período em dias: sempre input numérico (qualquer valor positivo).
  if (key === "periodDays") return null;

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
): string {
  if (current === undefined || current === null || current === "") {
    if (field.default !== undefined && field.default !== null) return String(field.default);
    return "";
  }
  return String(current);
}

type Props = {
  schema: DataParamSchema;
  values: Record<string, string | number | boolean | null | undefined> | undefined;
  inheritedKeys?: Set<string>;
  branchScope?: BranchScope | null;
  idPrefix?: string;
  /** ribbon = grade multi-coluna; pane = empilhado. */
  layout?: "ribbon" | "pane";
  onChange: (key: string, value: string) => void;
};

export function DataParamFields({
  schema,
  values,
  inheritedKeys = new Set(),
  branchScope = null,
  idPrefix = "td-data-param",
  layout = "pane",
  onChange,
}: Props) {
  const entries = Object.entries(schema);
  if (entries.length === 0) return null;

  const compact = layout === "ribbon";
  const selectClass = compact ? "delpi-ui-select--compact" : undefined;
  const nativeClass = compact ? "delpi-ui-native-control--compact" : undefined;

  const fields = entries.map(([key, field]) => {
    const inherited = inheritedKeys.has(key);
    const current = values?.[key];
    const label = `${field.label ?? key}${inherited ? " (herdado do slide)" : ""}`;
    const hint = hintForParam(key, field);
    const fieldId = `${idPrefix}-${key}`;
    const selectOptions = resolveParamSelectOptions(key, field);
    const displayValue = displayParamValue(current, field);

    if (BRANCH_PARAM_KEYS.has(key)) {
      return (
        <BranchField
          key={key}
          id={fieldId}
          label={label}
          hint={hint}
          scope={branchScope}
          value={displayValue}
          onChange={(value) => onChange(key, value)}
          placeholder={inherited ? "Herdado do slide" : "Ex.: 01"}
        />
      );
    }

    if (selectOptions) {
      const emptyLabel = inherited
        ? "Herdado do slide"
        : field.optional || field.default !== undefined
          ? "Opcional"
          : "Selecione…";
      const showEmpty =
        field.optional ||
        field.default !== undefined ||
        inherited ||
        !selectOptions.some((option) => option.value === displayValue);

      return (
        <DeckField key={key} id={fieldId} label={label} hint={hint}>
          <FormSelectControl
            id={fieldId}
            className={selectClass}
            ariaLabel={field.label ?? key}
            value={displayValue}
            onChange={(value: string) => onChange(key, value)}
            options={[
              ...(showEmpty ? [{ value: "", label: emptyLabel }] : []),
              ...selectOptions,
            ]}
          />
        </DeckField>
      );
    }

    const inputType = isDateParam(key, field)
      ? "date"
      : field.type === "integer" || field.type === "number"
        ? "number"
        : "text";

    return (
      <DeckField key={key} id={fieldId} label={label} hint={hint}>
        <NativeTextControl
          id={fieldId}
          type={inputType}
          className={nativeClass}
          placeholder={
            inherited
              ? "Herdado do slide"
              : field.default !== undefined
                ? `Padrão: ${field.default}`
                : field.optional
                  ? "Opcional"
                  : ""
          }
          value={current === undefined || current === null ? "" : String(current)}
          onChange={(value: string) => onChange(key, value)}
        />
      </DeckField>
    );
  });

  if (layout === "ribbon") {
    return <div className="td-deck-ribbon__field-grid">{fields}</div>;
  }

  return <>{fields}</>;
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
