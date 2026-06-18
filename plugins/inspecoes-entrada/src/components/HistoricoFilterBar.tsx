import { Filter, RotateCcw } from "lucide-react";

import type { HistoricoFilters } from "../types/inspecoesEntradaHistorico";

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

const RESULT_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "APROVADA", label: "Aprovada" },
  { value: "REJEITADA", label: "Rejeitada" },
] as const;

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
    <section className="ie-card ie-filter-bar" aria-label="Filtros do histórico">
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

      <div className="ie-filter-grid">
        <label className="ie-field">
          <span>Filial</span>
          <select
            value={branch}
            disabled={branchLocked}
            onChange={(event) => onBranchChange(event.target.value)}
          >
            <option value="01">01 — SC</option>
            <option value="02">02 — ES</option>
          </select>
        </label>

        <label className="ie-field">
          <span>Resultado</span>
          <select
            value={filters.result}
            onChange={(event) =>
              onChange({ result: event.target.value as HistoricoFilters["result"] })
            }
          >
            {RESULT_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="ie-field">
          <span>Data laudo (de)</span>
          <input
            type="date"
            value={filters.date_from}
            onChange={(event) => onChange({ date_from: event.target.value })}
          />
        </label>

        <label className="ie-field">
          <span>Data laudo (até)</span>
          <input
            type="date"
            value={filters.date_to}
            onChange={(event) => onChange({ date_to: event.target.value })}
          />
        </label>

        <label className="ie-field ie-field--wide">
          <span>Fornecedor</span>
          <input
            type="search"
            value={filters.supplier}
            placeholder="Nome do fornecedor"
            onChange={(event) => onChange({ supplier: event.target.value })}
          />
        </label>

        <label className="ie-field">
          <span>Produto</span>
          <input
            type="search"
            value={filters.product_code}
            placeholder="Código do produto"
            onChange={(event) => onChange({ product_code: event.target.value })}
          />
        </label>

        <label className="ie-field ie-field--wide">
          <span>Ensaiador</span>
          <input
            type="search"
            value={filters.inspector}
            placeholder="Nome do ensaiador"
            onChange={(event) => onChange({ inspector: event.target.value })}
          />
        </label>

        <label className="ie-field">
          <span>Nota fiscal</span>
          <input
            type="search"
            value={filters.invoice_number}
            placeholder="Ex.: 000042999"
            onChange={(event) => onChange({ invoice_number: event.target.value })}
          />
        </label>

        <label className="ie-field">
          <span>Lote</span>
          <input
            type="search"
            value={filters.lot}
            placeholder="Lote"
            onChange={(event) => onChange({ lot: event.target.value })}
          />
        </label>
      </div>
    </section>
  );
}
