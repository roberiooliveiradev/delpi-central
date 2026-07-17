import { NativeTextControl } from "@delpi/plugin-ui/index";
import { Columns3 } from "lucide-react";
import { useEffect, useState } from "react";

import type { DataQueryDraft } from "../domain/dataQueryTypes";

export function DataPrepareQueryList({
  drafts,
  activeQueryId,
  onSelect,
  onRename,
}: {
  drafts: DataQueryDraft[];
  activeQueryId: string | null;
  onSelect: (sourceId: string) => void;
  onRename: (name: string) => Promise<void>;
}) {
  const active = drafts.find((draft) => draft.sourceId === activeQueryId);
  const [name, setName] = useState(active?.queryName ?? "");
  useEffect(() => setName(active?.queryName ?? ""), [active?.queryName]);
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
      {active ? (
        <div className="td-data-pq__query-rename">
          <label htmlFor="td-query-name">Nome da consulta</label>
          <NativeTextControl
            id="td-query-name"
            value={name}
            aria-label="Nome da consulta ativa"
            onChange={setName}
            onKeyDown={(event) => {
              if (event.key === "Enter" && name.trim() && name.trim() !== active.queryName) {
                event.preventDefault();
                void onRename(name);
              } else if (event.key === "Escape") {
                setName(active.queryName);
              }
            }}
          />
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            disabled={!name.trim() || name.trim() === active.queryName}
            onClick={() => void onRename(name)}
          >
            Renomear
          </button>
        </div>
      ) : null}
    </aside>
  );
}
