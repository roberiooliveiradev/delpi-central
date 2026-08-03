import { NativeTextControl } from "@delpi/plugin-ui/index";
import type { BranchScope } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { TdNativeSelectField } from "./tdFormFields";

type Props = {
  id: string;
  label: string;
  hint?: string;
  scope: BranchScope | null;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  /** Enum do paramSchema da rota (OpenAPI) — fallback quando não há branchScope. */
  schemaEnum?: Array<string | number | boolean> | null;
  /**
   * Rótulo da opção vazia (Limpar filtro / Não definido / Valores diferentes).
   * Sempre há opção de limpar no select.
   */
  emptyOptionLabel?: string;
};

/** Opções de filial: RBAC (scope) ∩ enum da API, ou um dos dois. */
export function resolveBranchFieldOptions(
  scope: BranchScope | null | undefined,
  schemaEnum?: Array<string | number | boolean> | null,
): string[] {
  const scopeBranches = (scope?.branches ?? [])
    .map((item) => String(item).trim())
    .filter(Boolean);
  const schemaBranches = Array.isArray(schemaEnum)
    ? schemaEnum.map((item) => String(item).trim()).filter(Boolean)
    : [];

  if (scopeBranches.length > 0 && schemaBranches.length > 0) {
    const allowed = new Set(schemaBranches);
    const intersect = scopeBranches.filter((branch) => allowed.has(branch));
    return intersect.length > 0 ? intersect : scopeBranches;
  }
  if (scopeBranches.length > 0) return scopeBranches;
  return schemaBranches;
}

export function BranchField({
  id,
  label,
  hint,
  scope,
  value,
  onChange,
  placeholder,
  schemaEnum,
  emptyOptionLabel,
}: Props) {
  const branches = resolveBranchFieldOptions(scope, schemaEnum);
  const clearLabel = TV_DASHBOARD_HELP_TOOLTIPS.data.filterClear;
  const placeholderOption = emptyOptionLabel ?? clearLabel;

  if (branches.length > 0) {
    return (
      <TdNativeSelectField
        id={id}
        label={label}
        hint={hint}
        value={value}
        onChange={onChange}
        placeholderOption={placeholderOption}
        options={branches.map((branch) => ({
          value: branch,
          label: `Filial ${branch}`,
        }))}
      />
    );
  }

  const hasValue = String(value ?? "").trim() !== "";
  return (
    <DeckField id={id} label={label} hint={hint}>
      <div className="td-data-param-clearable">
        <NativeTextControl
          id={id}
          value={value}
          onChange={onChange}
          placeholder={placeholder ?? "Ex.: 01"}
        />
        {hasValue ? (
          <button
            type="button"
            className="td-data-param-clearable__btn"
            aria-label={clearLabel}
            title={clearLabel}
            onClick={() => onChange("")}
          >
            ×
          </button>
        ) : null}
      </div>
    </DeckField>
  );
}
