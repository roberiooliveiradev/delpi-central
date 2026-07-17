import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  NativeTextControl,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  ArrowDownAZ,
  ArrowDownZA,
  ArrowLeft,
  Columns3,
  Copy,
  Eraser,
  Filter,
  FilterX,
  Replace,
  TextCursorInput,
  Trash2,
  Type,
} from "lucide-react";
import { useEffect, useState } from "react";

import type { DataQueryInsertOperation } from "../domain/dataQueryTypes";

export type ColumnMenuTarget = {
  position: FixedPanelPoint;
  columnKey: string;
  columnLabel: string;
  columnType: string;
  cellValue: string | null;
};

type Insert = (
  stepName: string,
  operation: DataQueryInsertOperation,
  arguments_: Record<string, unknown>,
) => void;

type View = "root" | "rename" | "replace" | "type";

const COLUMN_TYPES = [
  { value: "text", label: "Texto" },
  { value: "number", label: "Número" },
  { value: "logical", label: "Lógico" },
  { value: "date", label: "Data" },
  { value: "datetime", label: "Data e hora" },
  { value: "duration", label: "Duração" },
  { value: "any", label: "Qualquer" },
];

function truncate(value: string): string {
  return value.length > 18 ? `${value.slice(0, 18)}…` : value;
}

export function DataPrepareColumnMenu({
  target,
  onClose,
  onInsert,
}: {
  target: ColumnMenuTarget | null;
  onClose: () => void;
  onInsert: Insert;
}) {
  const [view, setView] = useState<View>("root");
  const [renameTo, setRenameTo] = useState("");
  const [findValue, setFindValue] = useState("");
  const [replaceValue, setReplaceValue] = useState("");

  useEffect(() => {
    if (!target) return;
    setView("root");
    setRenameTo(target.columnLabel);
    setFindValue(target.cellValue ?? "");
    setReplaceValue("");
  }, [target]);

  if (!target) return null;

  const column = target.columnKey;
  const cellText = target.cellValue;
  const commit = (
    stepName: string,
    operation: DataQueryInsertOperation,
    arguments_: Record<string, unknown>,
  ) => {
    onInsert(stepName, operation, arguments_);
    onClose();
  };

  return (
    <ContextMenu
      open={Boolean(target)}
      position={target.position}
      onClose={onClose}
      aria-label={`Ações da coluna ${target.columnLabel}`}
      portalScopeClassName="dashboard-tv-dashboard"
    >
      {view === "root" ? (
        <>
          <ContextMenuItem
            label="Renomear coluna"
            icon={TextCursorInput}
            onSelect={() => setView("rename")}
          />
          <ContextMenuItem
            label="Ordenar crescente"
            icon={ArrowDownAZ}
            onSelect={() => commit("Linhas ordenadas", "sort", { column, direction: "asc" })}
          />
          <ContextMenuItem
            label="Ordenar decrescente"
            icon={ArrowDownZA}
            onSelect={() => commit("Linhas ordenadas", "sort", { column, direction: "desc" })}
          />
          <ContextMenuItem label="Alterar tipo" icon={Type} onSelect={() => setView("type")} />
          <ContextMenuDivider />
          {cellText != null ? (
            <>
              <ContextMenuItem
                label={`Manter linhas iguais a "${truncate(cellText)}"`}
                icon={Filter}
                onSelect={() =>
                  commit("Linhas filtradas", "filter", { column, cmp: "eq", value: cellText })
                }
              />
              <ContextMenuItem
                label={`Remover linhas iguais a "${truncate(cellText)}"`}
                icon={FilterX}
                onSelect={() =>
                  commit("Linhas filtradas", "filter", { column, cmp: "neq", value: cellText })
                }
              />
            </>
          ) : null}
          <ContextMenuItem
            label="Substituir valores"
            icon={Replace}
            onSelect={() => setView("replace")}
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label="Duplicar coluna"
            icon={Copy}
            onSelect={() =>
              commit("Coluna duplicada", "duplicate_column", {
                column,
                newName: `${target.columnLabel} cópia`,
              })
            }
          />
          <ContextMenuItem
            label="Manter somente esta coluna"
            icon={Columns3}
            onSelect={() => commit("Colunas selecionadas", "select", { columns: [column] })}
          />
          <ContextMenuItem
            label="Remover erros"
            icon={Eraser}
            onSelect={() => commit("Erros removidos", "remove_errors", { columns: [column] })}
          />
          <ContextMenuDivider />
          <ContextMenuItem
            label="Remover coluna"
            icon={Trash2}
            destructive
            onSelect={() => commit("Colunas removidas", "remove_columns", { columns: [column] })}
          />
        </>
      ) : null}

      {view === "rename" ? (
        <div className="td-data-pq__menu-view">
          <form
            className="td-data-pq__menu-form"
            onSubmit={(event) => {
              event.preventDefault();
              if (!renameTo.trim() || renameTo.trim() === target.columnLabel) return;
              commit("Colunas renomeadas", "rename", { from: column, to: renameTo.trim() });
            }}
          >
            <label htmlFor="td-col-rename">Novo nome de “{target.columnLabel}”</label>
            <NativeTextControl
              id="td-col-rename"
              autoFocus
              aria-label="Novo nome da coluna"
              value={renameTo}
              onChange={setRenameTo}
            />
            <div className="td-data-pq__menu-form-actions">
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                onClick={() => setView("root")}
              >
                <ArrowLeft size={14} aria-hidden /> Voltar
              </button>
              <button
                type="submit"
                className="td-btn td-btn--sm"
                disabled={!renameTo.trim() || renameTo.trim() === target.columnLabel}
              >
                Aplicar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {view === "replace" ? (
        <div className="td-data-pq__menu-view">
          <form
            className="td-data-pq__menu-form"
            onSubmit={(event) => {
              event.preventDefault();
              commit("Valor substituído", "replace", {
                column,
                find: findValue,
                replaceWith: replaceValue,
              });
            }}
          >
            <label htmlFor="td-col-find">Localizar</label>
            <NativeTextControl
              id="td-col-find"
              autoFocus
              aria-label="Valor a localizar"
              placeholder="Valor a localizar"
              value={findValue}
              onChange={setFindValue}
            />
            <label htmlFor="td-col-replace">Substituir por</label>
            <NativeTextControl
              id="td-col-replace"
              aria-label="Novo valor"
              placeholder="Novo valor"
              value={replaceValue}
              onChange={setReplaceValue}
            />
            <div className="td-data-pq__menu-form-actions">
              <button
                type="button"
                className="td-btn td-btn--sm td-btn--ghost"
                onClick={() => setView("root")}
              >
                <ArrowLeft size={14} aria-hidden /> Voltar
              </button>
              <button type="submit" className="td-btn td-btn--sm">
                Aplicar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {view === "type" ? (
        <>
          {COLUMN_TYPES.map((item) => (
            <ContextMenuItem
              key={item.value}
              label={item.label}
              onSelect={() => commit("Tipo alterado", "changeType", { column, to: item.value })}
            />
          ))}
          <ContextMenuDivider />
          <ContextMenuItem label="Voltar" icon={ArrowLeft} onSelect={() => setView("root")} />
        </>
      ) : null}
    </ContextMenu>
  );
}
