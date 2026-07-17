import {
  ContextMenu,
  ContextMenuItem,
  NativeTextControl,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import { Columns3, Pencil } from "lucide-react";
import { useState } from "react";

import type { DataQueryDraft } from "../domain/dataQueryTypes";

type QueryMenu = { position: FixedPanelPoint; sourceId: string };

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
  const [menu, setMenu] = useState<QueryMenu | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const startRename = (draft: DataQueryDraft) => {
    onSelect(draft.sourceId);
    setRenameValue(draft.queryName);
    setRenamingId(draft.sourceId);
    setMenu(null);
  };

  const commitRename = (draft: DataQueryDraft) => {
    const name = renameValue.trim();
    setRenamingId(null);
    if (name && name !== draft.queryName) void onRename(name);
  };

  return (
    <aside className="td-data-pq__queries" aria-label="Consultas">
      <h2 className="td-data-pq__pane-title">Consultas [{drafts.length}]</h2>
      <div className="td-data-pq__query-list" role="tablist" aria-orientation="vertical">
        {drafts.map((draft) => {
          const selected = draft.sourceId === activeQueryId;
          if (renamingId === draft.sourceId) {
            return (
              <div key={draft.sourceId} className="td-data-pq__query-rename-inline">
                <NativeTextControl
                  autoFocus
                  value={renameValue}
                  aria-label={`Novo nome de ${draft.queryName}`}
                  onChange={setRenameValue}
                  onBlur={() => setRenamingId(null)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      commitRename(draft);
                    } else if (event.key === "Escape") {
                      event.preventDefault();
                      setRenamingId(null);
                    }
                  }}
                />
              </div>
            );
          }
          return (
            <button
              key={draft.sourceId}
              type="button"
              role="tab"
              aria-selected={selected}
              className={
                selected
                  ? "td-data-pq__query td-data-pq__query--selected"
                  : "td-data-pq__query"
              }
              onClick={() => onSelect(draft.sourceId)}
              onDoubleClick={() => startRename(draft)}
              onContextMenu={(event) => {
                event.preventDefault();
                onSelect(draft.sourceId);
                setMenu({
                  position: { x: event.clientX, y: event.clientY },
                  sourceId: draft.sourceId,
                });
              }}
            >
              <Columns3 size={16} aria-hidden />
              <span className="td-data-pq__query-label">{draft.queryName}</span>
              {draft.dirty ? <span aria-label="Alterações não aplicadas">●</span> : null}
            </button>
          );
        })}
      </div>
      <ContextMenu
        open={Boolean(menu)}
        position={menu?.position ?? null}
        onClose={() => setMenu(null)}
        aria-label="Ações da consulta"
      >
        {menu ? (
          <ContextMenuItem
            label="Renomear"
            icon={Pencil}
            onSelect={() => {
              const draft = drafts.find((item) => item.sourceId === menu.sourceId);
              if (draft) startRename(draft);
            }}
          />
        ) : null}
      </ContextMenu>
    </aside>
  );
}
