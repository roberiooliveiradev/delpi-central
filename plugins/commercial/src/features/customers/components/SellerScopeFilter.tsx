import { CommercialSelectField } from "../../../app/commercialUi";

type SellerScopeFilterProps = {
  sellers: { id: string; display_name: string }[];
  value: string | null;
  onChange: (sellerId: string | null) => void;
};

export function SellerScopeFilter({ sellers, value, onChange }: SellerScopeFilterProps) {
  const options = sellers.map((seller) => ({
    value: seller.id,
    label: seller.display_name,
  }));

  return (
    <div className="pva-seller-scope" role="group" aria-label="Filtro de carteira">
      <CommercialSelectField
        label="Carteira"
        options={options}
        value={value ?? ""}
        onChange={(next) => onChange(next || null)}
        allowEmpty
        emptyLabel="Todos os vendedores"
        searchable={options.length > 8}
      />
    </div>
  );
}
