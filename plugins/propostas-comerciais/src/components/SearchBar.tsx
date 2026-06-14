import { Search } from "lucide-react";

type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  resultCount: number;
};

export function SearchBar({ value, onChange, resultCount }: SearchBarProps) {
  return (
    <div className="pc-search-bar">
      <label className="pc-search-bar__field">
        <Search size={18} aria-hidden="true" />
        <input
          type="search"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Buscar por OV, oportunidade, proposta ou cliente"
          aria-label="Buscar propostas comerciais"
        />
      </label>
      <span className="pc-search-bar__count">
        {resultCount.toLocaleString("pt-BR")} proposta(s)
      </span>
    </div>
  );
}
