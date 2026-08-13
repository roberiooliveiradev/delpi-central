import {
  CommercialMultiSelectField,
  CommercialSelectField,
} from "../../../app/commercialUi";

type SellerOption = { id: string; display_name: string };

type SellerScopeFilterBase = {
  sellers: SellerOption[];
  hint?: string;
  /** team/manage → «Todas as carteiras»; multi-própria → «Todas as minhas carteiras». */
  teamScope?: boolean;
  /**
   * Sobrescreve o rótulo da seleção vazia (ex.: analytics «Não filtrar»).
   * Sem valor, usa o padrão por teamScope.
   */
  emptyLabel?: string;
};

type SellerScopeFilterSingleProps = SellerScopeFilterBase & {
  multiple?: false;
  value: string | null;
  onChange: (sellerId: string | null) => void;
};

type SellerScopeFilterMultiProps = SellerScopeFilterBase & {
  multiple: true;
  selectedValues: string[];
  onChange: (sellerIds: string[]) => void;
};

export type SellerScopeFilterProps = SellerScopeFilterSingleProps | SellerScopeFilterMultiProps;

function emptyLabelForScope(teamScope: boolean): string {
  return teamScope ? "Todas as carteiras" : "Todas as minhas carteiras";
}

/** Rótulo da Visão geral / analytics: vazio = consolidado TOTVS sem membership. */
export const ANALYTICS_PORTFOLIO_FILTER_EMPTY_LABEL = "Não filtrar";

export function SellerScopeFilter(props: SellerScopeFilterProps) {
  const { sellers, hint, teamScope = false, emptyLabel: emptyLabelProp } = props;
  const options = sellers.map((seller) => ({
    value: seller.id,
    label: seller.display_name,
  }));
  const emptyLabel = emptyLabelProp ?? emptyLabelForScope(teamScope);

  if (props.multiple) {
    return (
      <div className="cm-customer-seller-scope" role="group" aria-label="Filtro de carteira">
        <CommercialMultiSelectField
          label="Carteira"
          hint={hint}
          options={options}
          selectedValues={props.selectedValues}
          onChange={props.onChange}
          emptyLabel={emptyLabel}
          searchable
        />
      </div>
    );
  }

  return (
    <div className="cm-customer-seller-scope" role="group" aria-label="Filtro de carteira">
      <CommercialSelectField
        label="Carteira"
        hint={hint}
        options={options}
        value={props.value ?? ""}
        onChange={(next) => props.onChange(next || null)}
        allowEmpty
        emptyLabel={emptyLabel}
        searchable={options.length > 8}
      />
    </div>
  );
}
