import type { PurchaseRequestsAccess } from "../security/purchaseRequestsAccess";
import type { PurchaseRequestRequesterOption } from "../types/purchaseRequests";
import { OVERALL_STAGE_VALUES } from "../types/purchaseRequests";
import type { UrlState } from "../utils/urlState";
import {
  PurchaseRequestsFilterInputField,
  PurchaseRequestsFilterMultiSelectField,
  PurchaseRequestsFilterSelectField,
  PurchaseRequestsFiltersRow,
} from "../ui/purchaseRequestsUi";
import { labelOverallStage, formatRequesterOptionLabel } from "../utils/labels";

type PurchaseRequestsFiltersProps = {
  state: UrlState;
  access: PurchaseRequestsAccess;
  requesterOptions: PurchaseRequestRequesterOption[];
  requestersLoading?: boolean;
  onChange: (patch: Partial<UrlState>) => void;
  onClear: () => void;
};

export function PurchaseRequestsFilters({
  state,
  access,
  requesterOptions,
  requestersLoading = false,
  onChange,
  onClear,
}: PurchaseRequestsFiltersProps) {
  const requesterSelectOptions = requesterOptions.map((item) => ({
    value: item.protheus_user_id,
    label: formatRequesterOptionLabel(item.name, item.code, item.protheus_user_id),
  }));

  return (
    <PurchaseRequestsFiltersRow
      trailing={
        <button type="button" className="pr-btn pr-btn--secondary" onClick={onClear}>
          Limpar filtros
        </button>
      }
    >
      <PurchaseRequestsFilterSelectField
        label="Filial"
        value={state.branch}
        onChange={(value) => onChange({ branch: value, page: 1 })}
        options={access.branches.map((branch) => ({
          value: branch.value,
          label: branch.label,
        }))}
      />
      <PurchaseRequestsFilterInputField
        label="De"
        type="date"
        value={state.date_from}
        onChange={(value) => onChange({ date_from: value, page: 1 })}
      />
      <PurchaseRequestsFilterInputField
        label="Até"
        type="date"
        value={state.date_to}
        onChange={(value) => onChange({ date_to: value, page: 1 })}
      />
      <PurchaseRequestsFilterMultiSelectField
        label="Solicitante"
        selectedValues={state.requester_user_ids}
        options={requesterSelectOptions}
        onChange={(values) => onChange({ requester_user_ids: values, page: 1 })}
        disabled={requestersLoading}
        searchable
        showBulkActions
      />
      <PurchaseRequestsFilterInputField
        label="Número da SC"
        type="text"
        value={state.request_number}
        onChange={(value) => onChange({ request_number: value, page: 1 })}
        placeholder="Ex.: 177030"
      />
      <PurchaseRequestsFilterInputField
        label="Centro de custo"
        type="text"
        value={state.cost_center}
        onChange={(value) => onChange({ cost_center: value, page: 1 })}
        placeholder="Código do CC"
      />
      <PurchaseRequestsFilterInputField
        label="Produto"
        type="text"
        value={state.product_code}
        onChange={(value) => onChange({ product_code: value, page: 1 })}
        placeholder="Código do produto"
      />
      <PurchaseRequestsFilterInputField
        label="Fornecedor"
        type="text"
        value={state.supplier_code}
        onChange={(value) => onChange({ supplier_code: value, page: 1 })}
        placeholder="Código do fornecedor"
      />
      <PurchaseRequestsFilterInputField
        label="Pedido de compra"
        type="text"
        value={state.order_number}
        onChange={(value) => onChange({ order_number: value, page: 1 })}
        placeholder="Número do PC"
      />
      <PurchaseRequestsFilterSelectField
        label="Situação"
        value={state.overall_stage}
        onChange={(value) =>
          onChange({
            overall_stage: (value as UrlState["overall_stage"]) || "",
            page: 1,
          })
        }
        options={[
          { value: "", label: "Todas" },
          ...OVERALL_STAGE_VALUES.map((stage) => ({
            value: stage,
            label: labelOverallStage(stage),
          })),
        ]}
      />
    </PurchaseRequestsFiltersRow>
  );
}
