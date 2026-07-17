import { Columns3 } from "lucide-react";

import type { DataQueryDraft } from "../domain/dataQueryTypes";

export function DataPrepareQueryList({
  drafts,
  activeQueryId,
  onSelect,
}: {
  drafts: DataQueryDraft[];
  activeQueryId: string | null;
  onSelect: (sourceId: string) => void;
}) {
  return (
    <aside className="td-data-pq__queries" aria-label="Consultas">
      <h2 className="td-data-pq__pane-title">Consultas [{drafts.length}]</h2>
      <div className="td-data-pq__query-list" role="tablist" aria-orientation="vertical">
        {drafts.map((draft) => (
          <button
            key={draft.sourceId}
            type="button"
            role="tab"
            aria-selected={draft.sourceId === activeQueryId}
            className={
              draft.sourceId === activeQueryId
                ? "td-data-pq__query td-data-pq__query--selected"
                : "td-data-pq__query"
            }
            onClick={() => onSelect(draft.sourceId)}
          >
            <Columns3 size={16} aria-hidden />
            <span className="td-data-pq__query-label">{draft.queryName}</span>
            {draft.dirty ? <span aria-label="Alterações não aplicadas">●</span> : null}
          </button>
        ))}
      </div>
    </aside>
  );
}
