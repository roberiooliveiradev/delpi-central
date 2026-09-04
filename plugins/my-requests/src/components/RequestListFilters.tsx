import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import {
  REQUEST_LIST_SEARCH_DEBOUNCE_MS,
  REQUEST_STATUS_FILTER_OPTIONS,
  type RequestListFiltersState,
} from "../content/requestListFilters";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsFilterInputField,
  MyRequestsFilterSelectField,
  MyRequestsFiltersRow,
} from "../ui/mrUi";

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
  const [searchDraft, setSearchDraft] = useState(filters.q);

  useEffect(() => {
    setSearchDraft(filters.q);
  }, [filters.q]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      const next = searchDraft.trim();
      const current = (filters.q || "").trim();
      if (next === current) return;
      onChange({ q: next, page: 1 });
    }, REQUEST_LIST_SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [searchDraft, filters.q, onChange]);

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
      <MyRequestsFilterInputField
        label="Busca"
        type="search"
        value={searchDraft}
        onChange={setSearchDraft}
        disabled={disabled}
        placeholder="Número, código, nome…"
      />
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
