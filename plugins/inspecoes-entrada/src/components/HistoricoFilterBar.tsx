import { Filter, RotateCcw } from "lucide-react";

import type { HistoricoFilters } from "../types/inspecoesEntradaHistorico";
import { FilterBarShell, FilterInputField, FilterSelectField } from "./filtersUi";

type HistoricoFilterBarProps = {
  branch: string;
  branchLocked: boolean;
  filters: HistoricoFilters;
  hasActiveFilters: boolean;
  loading: boolean;
  onBranchChange: (branch: string) => void;
  onChange: (patch: Partial<HistoricoFilters>) => void;
  onClear: () => void;
};

const BRANCH_OPTIONS = [
  { value: "01", label: "01 — SC" },
  { value: "02", label: "02 — ES" },
];

const RESULT_OPTIONS = [
  { value: "APROVADA", label: "Aprovada" },
  { value: "REJEITADA", label: "Rejeitada" },
];

export function HistoricoFilterBar({
  branch,
  branchLocked,
  filters,
  hasActiveFilters,
  loading,
  onBranchChange,
  onChange,
  onClear,
}: HistoricoFilterBarProps) {
  return (
    <FilterBarShell
      ariaLabel="Filtros do histórico"
      leading={
        <div className="ie-filter-bar__header">
          <div className="ie-filter-bar__title">
            <Filter size={18} aria-hidden="true" />
            <h2>Filtros</h2>
          </div>
          {hasActiveFilters ? (
            <button
              type="button"
              className="ie-btn ie-btn--ghost ie-btn--sm"
              onClick={onClear}
              disabled={loading}
            >
              <RotateCcw size={14} aria-hidden="true" />
              Limpar filtros
            </button>
          ) : null}
        </div>
      }
    >
      <FilterSelectField
        id="ie-filter-branch"
        label="Filial"
        value={branch}
        disabled={branchLocked}
        onChange={onBranchChange}
        options={BRANCH_OPTIONS}
      />
      <FilterSelectField
        id="ie-filter-result"
        label="Resultado"
        value={filters.result}
        onChange={(value) => onChange({ result: value as HistoricoFilters["result"] })}
        options={RESULT_OPTIONS}
        placeholderOption="Todos"
      />
      <FilterInputField
        id="ie-filter-date-from"
        label="Data laudo (de)"
        type="date"
        value={filters.date_from}
        onChange={(value) => onChange({ date_from: value })}
      />
      <FilterInputField
        id="ie-filter-date-to"
        label="Data laudo (até)"
        type="date"
        value={filters.date_to}
        onChange={(value) => onChange({ date_to: value })}
      />
      <FilterInputField
        id="ie-filter-supplier"
        label="Fornecedor"
        type="search"
        wide
        value={filters.supplier}
        placeholder="Nome do fornecedor"
        onChange={(value) => onChange({ supplier: value })}
      />
      <FilterInputField
        id="ie-filter-product"
        label="Produto"
        type="search"
        value={filters.product_code}
        placeholder="Código do produto"
        onChange={(value) => onChange({ product_code: value })}
      />
      <FilterInputField
        id="ie-filter-inspector"
        label="Ensaiador"
        type="search"
        wide
        value={filters.inspector}
        placeholder="Nome do ensaiador"
        onChange={(value) => onChange({ inspector: value })}
      />
      <FilterInputField
        id="ie-filter-invoice"
        label="Nota fiscal"
        type="search"
        value={filters.invoice_number}
        placeholder="Ex.: 000042999"
        onChange={(value) => onChange({ invoice_number: value })}
      />
      <FilterInputField
        id="ie-filter-lot"
        label="Lote"
        type="search"
        value={filters.lot}
        placeholder="Lote"
        onChange={(value) => onChange({ lot: value })}
      />
    </FilterBarShell>
  );
}
