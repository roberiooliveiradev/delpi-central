import type { BranchScope } from "../api/tvDashboardApi";
import { FieldLabel } from "@delpi/plugin-ui";

type Props = {
  id: string;
  label: string;
  hint?: string;
  scope: BranchScope | null;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function BranchField({ id, label, hint, scope, value, onChange, placeholder }: Props) {
  const branches = scope?.branches ?? [];
  const allowConsolidated = scope?.allowConsolidated ?? true;

  if (branches.length > 0) {
    return (
      <div className="td-field">
        <FieldLabel htmlFor={id} label={label} hint={hint} className="td-field__label" />
        <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
          {allowConsolidated ? <option value="">Consolidado</option> : null}
          {branches.map((branch) => (
            <option key={branch} value={branch}>
              Filial {branch}
            </option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div className="td-field">
      <FieldLabel htmlFor={id} label={label} hint={hint} className="td-field__label" />
      <input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder ?? "Ex.: 01"}
      />
    </div>
  );
}
