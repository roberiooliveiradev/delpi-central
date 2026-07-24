import { useState } from "react";
import { ChevronDown, Filter, RotateCcw } from "lucide-react";
import type { ListFilters } from "../../domain/types";
import { BRANCH_OPTIONS } from "../../domain/fiscal";
import { STATUS_LABELS } from "../../domain/status";
import { branchLabel } from "../../constants/branch";
import { hasActiveFilters } from "../format";

type Props = {
  value: ListFilters;
  lockedBranch?: string;
  onChange: (next: ListFilters) => void;
  onClear: () => void;
};

export function RequestFilters({
  value,
  lockedBranch,
  onChange,
  onClear,
}: Props) {
  const [open, setOpen] = useState(true);
  const active = hasActiveFilters(value, {
    branch: lockedBranch,
    status: "pending",
  });
  const set = (patch: Partial<ListFilters>) => {
    const next = { ...value, ...patch, page: 1 };
    if (lockedBranch) next.branch = lockedBranch;
    onChange(next);
  };

  return (
    <section
      className={`lnf-card lnf-filters${active ? " lnf-filters--active" : ""}`}
      aria-label="Filtros da fila"
      data-testid="queue-filters"
    >
      <div className="lnf-filters__chrome">
        <div className="lnf-filters__title">
          <Filter size={16} aria-hidden />
          <strong>Filtros</strong>
          {active ? (
            <span className="lnf-filters__active-pill" data-testid="filters-active">
              Ativos
            </span>
          ) : null}
        </div>
        <div className="lnf-filters__chrome-actions">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost lnf-btn--sm"
            onClick={onClear}
            disabled={!active}
          >
            <RotateCcw size={14} aria-hidden />
            Limpar filtros
          </button>
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost lnf-btn--sm lnf-filters__toggle"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <ChevronDown
              size={16}
              aria-hidden
              className={open ? undefined : "lnf-filters__chevron--closed"}
            />
            {open ? "Recolher" : "Expandir"}
          </button>
        </div>
      </div>

      {open ? (
        <div className="lnf-filters__body">
          <div className="lnf-filters__row" data-testid="filters-primary">
            <label className="lnf-field">
              Filial
              {lockedBranch ? (
                <select
                  aria-label="Filial"
                  value={lockedBranch}
                  disabled
                  title="Filial definida pela rota do menu"
                >
                  <option value={lockedBranch}>{branchLabel(lockedBranch)}</option>
                </select>
              ) : (
                <select
                  aria-label="Filial"
                  value={value.branch ?? ""}
                  onChange={(e) => set({ branch: e.target.value || undefined })}
                >
                  <option value="">Todas</option>
                  {BRANCH_OPTIONS.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </select>
              )}
            </label>
            <label className="lnf-field">
              Status
              <select
                aria-label="Status"
                value={value.status ?? ""}
                onChange={(e) => set({ status: e.target.value || undefined })}
              >
                <option value="">Todos</option>
                {Object.entries(STATUS_LABELS).map(([k, label]) => (
                  <option key={k} value={k}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="lnf-field">
              Fornecedor
              <input
                type="search"
                value={value.supplier ?? ""}
                placeholder="Código ou nome"
                onChange={(e) => set({ supplier: e.target.value })}
              />
            </label>
            <label className="lnf-field">
              Número da nota
              <input
                type="search"
                inputMode="numeric"
                value={value.document ?? ""}
                placeholder="Somente números"
                onChange={(e) =>
                  set({ document: e.target.value.replace(/\D/g, "").slice(0, 9) })
                }
              />
            </label>
          </div>

          <div className="lnf-filters__row lnf-filters__row--dates" data-testid="filters-dates">
            <label className="lnf-field">
              Emissão de
              <input
                type="date"
                value={value.issued_from ?? ""}
                onChange={(e) => set({ issued_from: e.target.value || undefined })}
              />
            </label>
            <label className="lnf-field">
              Emissão até
              <input
                type="date"
                value={value.issued_to ?? ""}
                onChange={(e) => set({ issued_to: e.target.value || undefined })}
              />
            </label>
            <label className="lnf-field">
              Recebimento de
              <input
                type="date"
                value={value.received_from?.slice(0, 10) ?? ""}
                onChange={(e) =>
                  set({
                    received_from: e.target.value
                      ? `${e.target.value}T00:00:00`
                      : undefined,
                  })
                }
              />
            </label>
            <label className="lnf-field">
              Recebimento até
              <input
                type="date"
                value={value.received_to?.slice(0, 10) ?? ""}
                onChange={(e) =>
                  set({
                    received_to: e.target.value
                      ? `${e.target.value}T23:59:59`
                      : undefined,
                  })
                }
              />
            </label>
          </div>
        </div>
      ) : null}
    </section>
  );
}
