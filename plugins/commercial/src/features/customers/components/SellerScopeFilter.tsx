import { CommercialSelectField } from "../../../app/commercialUi";

type SellerScopeFilterProps = {
  sellers: { id: string; display_name: string }[];
  value: string | null;
  onChange: (sellerId: string | null) => void;
  hint?: string;
  /** team/manage → «Todas as carteiras»; multi-própria → «Todas as minhas carteiras». */
  teamScope?: boolean;
};

export function SellerScopeFilter({
  sellers,
  value,
  onChange,
  hint,
  teamScope = false,
}: SellerScopeFilterProps) {
  const options = sellers.map((seller) => ({
    value: seller.id,
    label: seller.display_name,
  }));

  return (
    <div className="cm-customer-seller-scope" role="group" aria-label="Filtro de carteira">
      <CommercialSelectField
        label="Carteira"
        hint={hint}
        options={options}
        value={value ?? ""}
        onChange={(next) => onChange(next || null)}
        allowEmpty
        emptyLabel={teamScope ? "Todas as carteiras" : "Todas as minhas carteiras"}
        searchable={options.length > 8}
      />
    </div>
  );
}
