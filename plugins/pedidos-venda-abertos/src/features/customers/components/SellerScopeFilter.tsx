type SellerScopeFilterProps = {
  sellers: { id: string; display_name: string }[];
  value: string | null;
  onChange: (sellerId: string | null) => void;
};

export function SellerScopeFilter({ sellers, value, onChange }: SellerScopeFilterProps) {
  return (
    <div className="pva-seller-scope" role="group" aria-label="Filtro de carteira">
      <label className="pva-seller-scope__label" htmlFor="pva-seller-scope">
        Carteira
      </label>
      <select
        id="pva-seller-scope"
        className="pva-seller-scope__select"
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value || null)}
      >
        <option value="">Todos os vendedores</option>
        {sellers.map((seller) => (
          <option key={seller.id} value={seller.id}>
            {seller.display_name}
          </option>
        ))}
      </select>
    </div>
  );
}
