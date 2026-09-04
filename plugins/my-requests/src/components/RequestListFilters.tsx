import { ActionButton } from "@delpi/plugin-ui/index";

import {
  REQUEST_STATUS_FILTER_OPTIONS,
  type RequestListFiltersState,
} from "../content/requestListFilters";
import type { RequestTypeSummary } from "../types/requests";
import { MyRequestsFilterSelectField, MyRequestsFiltersRow } from "../ui/mrUi";

type RequestListFiltersProps = {
  filters: RequestListFiltersState;
  types: RequestTypeSummary[];
  branches: string[];
  disabled?: boolean;
  onChange: (patch: Partial<RequestListFiltersState>) => void;
  onClear: () => void;
};

export function RequestListFilters({
  filters,
  types,
  branches,
  disabled,
  onChange,
  onClear,
}: RequestListFiltersProps) {
  const typeOptions = [
    { value: "", label: "Todos" },
    ...types.map((item) => ({ value: item.code, label: item.name })),
  ];
  const branchOptions = [
    { value: "", label: "Todas" },
    ...(branches.length ? branches : ["01", "02"]).map((code) => ({
      value: code,
      label: code,
    })),
  ];
  const statusOptions = REQUEST_STATUS_FILTER_OPTIONS.map((item) => ({
    value: item.value,
    label: item.label,
  }));

  return (
    <MyRequestsFiltersRow
      trailing={
        <ActionButton type="button" variant="ghost" disabled={disabled} onClick={onClear}>
          Limpar filtros
        </ActionButton>
      }
    >
      <MyRequestsFilterSelectField
        label="Tipo"
        value={filters.typeCode}
        onChange={(value) => onChange({ typeCode: value, page: 1 })}
        options={typeOptions}
        disabled={disabled}
      />
      <MyRequestsFilterSelectField
        label="Status"
        value={filters.status}
        onChange={(value) => onChange({ status: value, page: 1 })}
        options={statusOptions}
        disabled={disabled}
      />
      <MyRequestsFilterSelectField
        label="Filial"
        value={filters.branch}
        onChange={(value) => onChange({ branch: value, page: 1 })}
        options={branchOptions}
        disabled={disabled}
      />
    </MyRequestsFiltersRow>
  );
}
