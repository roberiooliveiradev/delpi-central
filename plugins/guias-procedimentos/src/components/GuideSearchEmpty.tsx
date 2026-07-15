import { SearchX } from "lucide-react";

import {
  CLEAR_SEARCH_LABEL,
  SEARCH_EMPTY_MESSAGE,
  SEARCH_EMPTY_TITLE,
} from "../content/catalog";

type GuideSearchEmptyProps = {
  onClear?: () => void;
};

export function GuideSearchEmpty({ onClear }: GuideSearchEmptyProps) {
  return (
    <div className="gp-empty" role="status">
      <SearchX size={22} strokeWidth={1.75} aria-hidden="true" />
      <p className="gp-empty__title">{SEARCH_EMPTY_TITLE}</p>
      <p className="gp-empty__message">{SEARCH_EMPTY_MESSAGE}</p>
      {onClear ? (
        <button
          type="button"
          className="gp-btn gp-btn--ghost gp-empty__clear"
          onClick={onClear}
        >
          {CLEAR_SEARCH_LABEL}
        </button>
      ) : null}
    </div>
  );
}
