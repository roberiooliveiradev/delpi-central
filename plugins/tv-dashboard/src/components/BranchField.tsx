import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { BranchScope } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import {
  buildFilterSelectOptions,
  canClearFilterValue,
  normalizeFilterSelectChange,
  resolveFilterSelectValue,
} from "../utils/dataParamFilterUi";
import { DeckField } from "./deck/DeckField";

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
   * Rótulo da opção vazia (Limpar filtro / Não definido).
   * Sempre há opção de limpar — nunca confundir com «Valores diferentes».
   */
  emptyOptionLabel?: string;
  /** Multi-seleção: fontes discordam neste campo. */
  diverged?: boolean;
  divergedLabel?: string;
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
  diverged = false,
  divergedLabel,
}: Props) {
  const branches = resolveBranchFieldOptions(scope, schemaEnum);
  const clearLabel = emptyOptionLabel ?? TV_DASHBOARD_HELP_TOOLTIPS.data.filterClear;
  const differLabel = divergedLabel ?? TV_DASHBOARD_HELP_TOOLTIPS.data.filterValuesDiffer;

  if (branches.length > 0) {
    const options = buildFilterSelectOptions(
      branches.map((branch) => ({
        value: branch,
        label: `Filial ${branch}`,
      })),
      {
        clearLabel,
        diverged,
        divergedLabel: differLabel,
      },
    );
    return (
      <DeckField id={id} label={label} hint={hint}>
        <FormSelectControl
          id={id}
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          ariaLabel={label}
          value={resolveFilterSelectValue(value, diverged)}
          onChange={(next) => {
            const normalized = normalizeFilterSelectChange(next);
            if (normalized === null) return;
            onChange(normalized);
          }}
          options={options}
        />
      </DeckField>
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
          placeholder={placeholder ?? (diverged ? differLabel : "Ex.: 01")}
        />
        {canClearFilterValue({ diverged, hasStoredValue: hasValue }) ? (
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
