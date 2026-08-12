import { HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  SHIPMENT_STATUS_LABELS,
  type ShipmentStatus,
  type ThirdPartyMaterialsQuery,
} from "../types/thirdPartyMaterials";
import { branchLabel } from "../utils/formatters";
import {
  FilterBarShell,
  FilterCheckboxField,
  FilterInputField,
  FilterSelectField,
} from "./filtersUi";

type ShipmentFiltersProps = {
  filters: ThirdPartyMaterialsQuery;
  authorizedBranches: string[];
  loading?: boolean;
  onChange: (patch: Partial<ThirdPartyMaterialsQuery>) => void;
  onClear: () => void;
};

const STATUS_OPTIONS = Object.entries(SHIPMENT_STATUS_LABELS).map(([value, label]) => ({
  value,
  label,
}));

export function ShipmentFilters({
  filters,
  authorizedBranches,
  loading = false,
  onChange,
  onClear,
}: ShipmentFiltersProps) {
  const branchOptions = authorizedBranches.map((branch) => ({
    value: branch,
    label: branchLabel(branch),
  }));

  return (
    <FilterBarShell>
      <div className="mt-filters__primary">
        <FilterSelectField
          id="mt-filter-branch"
          label="Filial"
          hint={HELP_TOOLTIPS.filters.branch}
          value={filters.branch}
          options={branchOptions}
          placeholderOption="Selecione a filial"
          onChange={(value) => onChange({ branch: value })}
          disabled={loading || branchOptions.length === 0}
        />
        <FilterInputField
          id="mt-filter-product"
          label="Produto"
          hint={HELP_TOOLTIPS.filters.product}
          type="search"
          value={filters.product}
          placeholder="Ex.: 10211413"
          onChange={(value) => onChange({ product: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-customer-ref"
          label="Ref. cliente"
          hint={HELP_TOOLTIPS.filters.customerReference}
          type="search"
          value={filters.customerReference}
          placeholder="Ex.: 10018137"
          onChange={(value) => onChange({ customerReference: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-receipt"
          label="NF recebimento"
          hint={HELP_TOOLTIPS.filters.receipt}
          type="search"
          value={filters.receiptNumber}
          placeholder="Número da NF de entrada"
          onChange={(value) => onChange({ receiptNumber: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-return"
          label="NF retorno"
          hint={HELP_TOOLTIPS.filters.returnNf}
          type="search"
          value={filters.returnNumber}
          placeholder="Número da NF de retorno"
          onChange={(value) => onChange({ returnNumber: value })}
          disabled={loading || !filters.branch}
        />
      </div>

      <div className="mt-filters__secondary">
        <FilterInputField
          id="mt-filter-partner"
          label="Cliente"
          hint={HELP_TOOLTIPS.filters.partner}
          type="search"
          value={filters.partnerCode}
          placeholder="Código SA1"
          onChange={(value) => onChange({ partnerCode: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-store"
          label="Loja"
          type="search"
          value={filters.partnerStore}
          placeholder="Loja"
          onChange={(value) => onChange({ partnerStore: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-from"
          label="Emitida de"
          hint={HELP_TOOLTIPS.filters.period}
          type="date"
          value={filters.issuedFrom}
          onChange={(value) => onChange({ issuedFrom: value })}
          disabled={loading || !filters.branch}
        />
        <FilterInputField
          id="mt-filter-to"
          label="Emitida até"
          type="date"
          value={filters.issuedTo}
          onChange={(value) => onChange({ issuedTo: value })}
          disabled={loading || !filters.branch}
        />
        <FilterSelectField
          id="mt-filter-status"
          label="Status"
          hint={HELP_TOOLTIPS.filters.status}
          value={filters.status}
          options={STATUS_OPTIONS}
          placeholderOption="Todos"
          onChange={(value) => onChange({ status: value as ShipmentStatus | "" })}
          disabled={loading || !filters.branch}
        />
        <FilterCheckboxField
          id="mt-filter-balance"
          label="Somente com saldo"
          hint={HELP_TOOLTIPS.filters.onlyBalance}
          checked={filters.onlyWithBalance}
          onChange={(checked) => onChange({ onlyWithBalance: checked })}
          disabled={loading || !filters.branch}
        />
        <FilterCheckboxField
          id="mt-filter-test"
          label="Incluir produtos de teste"
          hint={HELP_TOOLTIPS.filters.testProducts}
          checked={filters.includeTestProducts}
          onChange={(checked) => onChange({ includeTestProducts: checked })}
          disabled={loading || !filters.branch}
        />
        <div className="mt-filters__actions">
          <button
            type="button"
            className="mt-btn mt-btn--secondary"
            onClick={onClear}
            disabled={loading}
          >
            Limpar
          </button>
        </div>
      </div>
    </FilterBarShell>
  );
}
