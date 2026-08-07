import { useState } from "react";
import { Filter, RotateCcw } from "lucide-react";
import { ActionButton, HelpTooltip } from "@delpi/plugin-ui/index";

import {
  CommercialDateField,
  CommercialFilterBarShell,
  CommercialMultiSelectField,
  CommercialSelectField,
  CommercialTextField,
} from "../app/commercialUi";
import { CM_HELP } from "../content/helpTooltips";
import type { ClientOption, OpenOrdersTotvsFilters } from "../utils/filterItems";
import type { StockFilter } from "../utils/statusBadges";

type FilterBarProps = {
  filters: OpenOrdersTotvsFilters;
  filiais: string[];
  clients: ClientOption[];
  hasActiveFilters: boolean;
  onChange: (patch: Partial<OpenOrdersTotvsFilters>) => void;
  onReset: () => void;
};

const STOCK_OPTIONS: Array<{ value: StockFilter; label: string }> = [
  { value: "com_estoque", label: "Pode faturar / com estoque" },
  { value: "parcial", label: "Estoque parcial" },
  { value: "sem_estoque", label: "Sem estoque / atrasado" },
];

export function FilterBar({
  filters,
  filiais,
  clients,
  hasActiveFilters,
  onChange,
  onReset,
}: FilterBarProps) {
  const [showMore, setShowMore] = useState(false);
  const filialOptions = filiais.map((filial) => ({ value: filial, label: filial }));
  const clientOptions = clients.map((client) => ({
    value: client.key,
    label: client.name,
  }));

  return (
    <CommercialFilterBarShell
      leading={
        <div className="cm-filter-bar__header">
          <div className="cm-filter-bar__title">
            <Filter size={18} aria-hidden="true" />
            <h2>Filtros</h2>
            <HelpTooltip content={CM_HELP.openOrders.filters} ariaLabel="Ajuda: Filtros" />
          </div>
          <div className="cm-filter-bar__header-actions">
            <ActionButton variant="ghost" onClick={() => setShowMore((v) => !v)}>
              {showMore ? "Menos filtros" : "Mais filtros"}
            </ActionButton>
            {hasActiveFilters ? (
              <ActionButton variant="ghost" onClick={onReset}>
                <RotateCcw size={14} aria-hidden="true" />
                Limpar
              </ActionButton>
            ) : null}
          </div>
        </div>
      }
    >
      <CommercialTextField
        label="Busca livre"
        hint={CM_HELP.openOrders.filterSearch}
        value={filters.search}
        placeholder="Cliente, pedido, produto, código…"
        onChange={(value) => onChange({ search: value })}
      />
      <CommercialSelectField
        label="Filial"
        hint={CM_HELP.openOrders.filterBranch}
        value={filters.filial}
        onChange={(value) => onChange({ filial: value })}
        options={filialOptions}
        allowEmpty
        emptyLabel="Todas"
      />
      <CommercialMultiSelectField
        label="Cliente"
        hint={CM_HELP.openOrders.filterClient}
        options={clientOptions}
        selectedValues={filters.clientCodes}
        onChange={(clientCodes) => onChange({ clientCodes })}
      />
      <CommercialDateField
        label="Entrega de"
        hint={CM_HELP.openOrders.filterDateStart}
        value={filters.dateStart}
        onChange={(value) => onChange({ dateStart: value })}
      />
      <CommercialDateField
        label="Entrega até"
        hint={CM_HELP.openOrders.filterDateEnd}
        value={filters.dateEnd}
        onChange={(value) => onChange({ dateEnd: value })}
      />

      {showMore ? (
        <>
          <CommercialSelectField
            label="Status da linha"
            hint={CM_HELP.openOrders.filterStock}
            value={filters.stockStatus}
            onChange={(value) =>
              onChange({
                stockStatus: value as StockFilter,
                lateOnly: value ? false : filters.lateOnly,
              })
            }
            options={STOCK_OPTIONS}
            allowEmpty
            emptyLabel="Todos os status"
          />
          <CommercialSelectField
            label="Entrega"
            hint={CM_HELP.openOrders.filterLate}
            value={filters.lateOnly ? "late" : ""}
            onChange={(value) =>
              onChange({
                lateOnly: value === "late",
                stockStatus: value === "late" ? "" : filters.stockStatus,
              })
            }
            options={[{ value: "late", label: "Em atraso" }]}
            allowEmpty
            emptyLabel="Todas"
          />
        </>
      ) : null}
    </CommercialFilterBarShell>
  );
}
