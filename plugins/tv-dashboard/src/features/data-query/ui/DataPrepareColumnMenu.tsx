import {
  FormSelectControl,
  NativeTextControl,
  useClickOutside,
  useDelpiUiPortalTheme,
  useFixedPanelPosition,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  ArrowDownAZ,
  ArrowDownZA,
  Columns3,
  Copy,
  Eraser,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { DataQueryInsertOperation } from "../domain/dataQueryTypes";

export type ColumnMenuTarget = {
  position: FixedPanelPoint;
  columnKey: string;
  columnLabel: string;
  columnType: string;
};

type Insert = (
  stepName: string,
  operation: DataQueryInsertOperation,
  arguments_: Record<string, unknown>,
) => void;

const FILTER_COMPARATORS = [
  { value: "eq", label: "Igual a" },
  { value: "neq", label: "Diferente de" },
  { value: "contains", label: "Contém" },
  { value: "startsWith", label: "Começa com" },
  { value: "gt", label: "Maior que" },
  { value: "lt", label: "Menor que" },
];

const COLUMN_TYPES = [
  { value: "text", label: "Texto" },
  { value: "number", label: "Número" },
  { value: "logical", label: "Lógico" },
  { value: "date", label: "Data" },
  { value: "datetime", label: "Data e hora" },
  { value: "duration", label: "Duração" },
  { value: "any", label: "Qualquer" },
];

const VALUELESS_COMPARATORS = new Set<string>();

export function DataPrepareColumnMenu({
  target,
  onClose,
  onInsert,
}: {
  target: ColumnMenuTarget | null;
  onClose: () => void;
  onInsert: Insert;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const open = Boolean(target);
  const style = useFixedPanelPosition(open, target?.position ?? null, panelRef, 2);
  const theme = useDelpiUiPortalTheme(open);
  const [renameTo, setRenameTo] = useState("");
  const [comparator, setComparator] = useState("eq");
  const [filterValue, setFilterValue] = useState("");
  const [findValue, setFindValue] = useState("");
  const [replaceValue, setReplaceValue] = useState("");
  const [columnType, setColumnType] = useState("text");

  useClickOutside([panelRef], open, onClose);

  useEffect(() => {
    if (!target) return;
    setRenameTo(target.columnLabel);
    setComparator("eq");
    setFilterValue("");
    setFindValue("");
    setReplaceValue("");
    setColumnType(COLUMN_TYPES.some((item) => item.value === target.columnType)
      ? target.columnType
      : "text");
  }, [target]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  if (!target || typeof document === "undefined") return null;

  const column = target.columnKey;
  const commit = (
    stepName: string,
    operation: DataQueryInsertOperation,
    arguments_: Record<string, unknown>,
  ) => {
    onInsert(stepName, operation, arguments_);
    onClose();
  };
  const filterNeedsValue = !VALUELESS_COMPARATORS.has(comparator);

  return createPortal(
    <div
      className={["dashboard-tv-dashboard", theme.hostClassName].filter(Boolean).join(" ")}
      style={theme.style}
      data-theme={theme.dataTheme}
    >
      <div
        ref={panelRef}
        className="td-data-pq__col-menu"
        style={style}
        role="dialog"
        aria-label={`Editar coluna ${target.columnLabel}`}
      >
        <header className="td-data-pq__col-menu-head">
          <span className="td-data-pq__col-menu-title">{target.columnLabel}</span>
          <span className="td-data-pq__col-menu-type">{target.columnType}</span>
        </header>

        <div className="td-data-pq__col-menu-quick" role="group" aria-label="Ações rápidas">
          <button
            type="button"
            aria-label="Ordenar crescente"
            onClick={() => commit("Linhas ordenadas", "sort", { column, direction: "asc" })}
          >
            <ArrowDownAZ size={16} aria-hidden />
          </button>
          <button
            type="button"
            aria-label="Ordenar decrescente"
            onClick={() => commit("Linhas ordenadas", "sort", { column, direction: "desc" })}
          >
            <ArrowDownZA size={16} aria-hidden />
          </button>
          <button
            type="button"
            aria-label="Manter somente esta coluna"
            onClick={() => commit("Colunas selecionadas", "select", { columns: [column] })}
          >
            <Columns3 size={16} aria-hidden />
          </button>
          <button
            type="button"
            aria-label="Duplicar coluna"
            onClick={() =>
              commit("Coluna duplicada", "duplicate_column", {
                column,
                newName: `${target.columnLabel} cópia`,
              })
            }
          >
            <Copy size={16} aria-hidden />
          </button>
          <button
            type="button"
            aria-label="Remover linhas com erro"
            onClick={() => commit("Erros removidos", "remove_errors", { columns: [column] })}
          >
            <Eraser size={16} aria-hidden />
          </button>
          <button
            type="button"
            className="td-data-pq__col-menu-danger"
            aria-label="Remover coluna"
            onClick={() => commit("Colunas removidas", "remove_columns", { columns: [column] })}
          >
            <Trash2 size={16} aria-hidden />
          </button>
        </div>

        <form
          className="td-data-pq__col-menu-field"
          onSubmit={(event) => {
            event.preventDefault();
            if (!renameTo.trim() || renameTo.trim() === target.columnLabel) return;
            commit("Colunas renomeadas", "rename", { from: column, to: renameTo.trim() });
          }}
        >
          <label htmlFor="td-col-rename">Renomear</label>
          <div className="td-data-pq__col-menu-row">
            <NativeTextControl
              id="td-col-rename"
              aria-label="Novo nome da coluna"
              value={renameTo}
              onChange={setRenameTo}
            />
            <button type="submit" className="td-btn td-btn--sm">
              Aplicar
            </button>
          </div>
        </form>

        <form
          className="td-data-pq__col-menu-field"
          onSubmit={(event) => {
            event.preventDefault();
            commit("Linhas filtradas", "filter", {
              column,
              cmp: comparator,
              value: filterValue,
            });
          }}
        >
          <label htmlFor="td-col-filter">Filtrar linhas</label>
          <div className="td-data-pq__col-menu-row">
            <FormSelectControl
              id="td-col-filter-cmp"
              ariaLabel="Comparador do filtro"
              value={comparator}
              onChange={setComparator}
              options={FILTER_COMPARATORS}
            />
          </div>
          <div className="td-data-pq__col-menu-row">
            <NativeTextControl
              id="td-col-filter"
              aria-label="Valor do filtro"
              placeholder="Valor"
              value={filterValue}
              disabled={!filterNeedsValue}
              onChange={setFilterValue}
            />
            <button type="submit" className="td-btn td-btn--sm">
              Filtrar
            </button>
          </div>
        </form>

        <form
          className="td-data-pq__col-menu-field"
          onSubmit={(event) => {
            event.preventDefault();
            commit("Valor substituído", "replace", {
              column,
              find: findValue,
              replaceWith: replaceValue,
            });
          }}
        >
          <label htmlFor="td-col-find">Substituir valor</label>
          <div className="td-data-pq__col-menu-row">
            <NativeTextControl
              id="td-col-find"
              aria-label="Valor a localizar"
              placeholder="Localizar"
              value={findValue}
              onChange={setFindValue}
            />
            <NativeTextControl
              id="td-col-replace"
              aria-label="Novo valor"
              placeholder="Substituir por"
              value={replaceValue}
              onChange={setReplaceValue}
            />
            <button type="submit" className="td-btn td-btn--sm">
              Aplicar
            </button>
          </div>
        </form>

        <form
          className="td-data-pq__col-menu-field"
          onSubmit={(event) => {
            event.preventDefault();
            commit("Tipo alterado", "changeType", { column, to: columnType });
          }}
        >
          <label htmlFor="td-col-type">Alterar tipo</label>
          <div className="td-data-pq__col-menu-row">
            <FormSelectControl
              id="td-col-type"
              ariaLabel="Novo tipo da coluna"
              value={columnType}
              onChange={setColumnType}
              options={COLUMN_TYPES}
            />
            <button type="submit" className="td-btn td-btn--sm">
              Aplicar
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}
