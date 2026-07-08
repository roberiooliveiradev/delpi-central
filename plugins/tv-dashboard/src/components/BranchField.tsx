import type { BranchScope } from "../api/tvDashboardApi";
import { TdNativeSelectField, TdNativeTextField } from "./tdFormFields";

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
      <TdNativeSelectField
        id={id}
        label={label}
        hint={hint}
        value={value}
        onChange={onChange}
        placeholderOption={allowConsolidated ? "Consolidado" : undefined}
        options={branches.map((branch) => ({
          value: branch,
          label: `Filial ${branch}`,
        }))}
      />
    );
  }

  return (
    <TdNativeTextField
      id={id}
      label={label}
      hint={hint}
      value={value}
      onChange={onChange}
      placeholder={placeholder ?? "Ex.: 01"}
    />
  );
}
