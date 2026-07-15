import { Search } from "lucide-react";

import { SEARCH_PLACEHOLDER } from "../content/catalog";

type GuideSearchFieldProps = {
  value: string;
  onChange: (value: string) => void;
};

export function GuideSearchField({ value, onChange }: GuideSearchFieldProps) {
  return (
    <label className="gp-search gp-no-print-hide">
      <span className="gp-visually-hidden">Buscar guias</span>
      <Search
        className="gp-search__icon"
        size={18}
        strokeWidth={2}
        aria-hidden="true"
      />
      <input
        className="gp-search__input"
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={SEARCH_PLACEHOLDER}
        autoComplete="off"
        enterKeyHint="search"
      />
    </label>
  );
}
