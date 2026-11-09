import {
  ArrowDownAZ,
  ArrowUpAZ,
  Grid2X2,
  LayoutGrid,
  LayoutList,
  Rows3,
} from "lucide-react";
import { FieldLabel } from "@delpi/plugin-ui/index";

import { SelectField } from "../../components/ui/SelectField";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  PROCESSO_LIST_SORT_OPTIONS,
  type ProcessoListSort,
  type ProcessoListSortField,
} from "./processListSort";
import {
  PROCESSO_LIST_VIEW_MODES,
  type ProcessoListViewMode,
} from "./processListViewMode";

export type ProcessListPresentationPart = "sort-field" | "sort-direction" | "view-modes";

const ALL_PARTS: ProcessListPresentationPart[] = [
  "sort-field",
  "sort-direction",
  "view-modes",
];

type Props = {
  sort: ProcessoListSort;
  onSortFieldChange: (field: ProcessoListSortField) => void;
  onToggleSortDirection: () => void;
  /** When true, sort field is locked to department name. */
  departmentRoot?: boolean;
  viewMode: ProcessoListViewMode;
  onViewModeChange: (mode: ProcessoListViewMode) => void;
  /** Subset of controls to render (default: all). Enables hero band composition. */
  parts?: ProcessListPresentationPart[];
};

function viewModeIcon(mode: ProcessoListViewMode) {
  switch (mode) {
    case "icons-lg":
      return LayoutGrid;
    case "icons-md":
      return Grid2X2;
    case "list":
      return LayoutList;
    default:
      return Rows3;
  }
}

/** Sort + view-mode controls — presentation-only; state owned by the page/Hero. */
export function ProcessListPresentationControls({
  sort,
  onSortFieldChange,
  onToggleSortDirection,
  departmentRoot = false,
  viewMode,
  onViewModeChange,
  parts = ALL_PARTS,
}: Props) {
  const P = TM_HELP_TOOLTIPS.processos;
  const sortDirectionLabel = sort.direction === "asc" ? "Menor → maior" : "Maior → menor";
  const showSortField = parts.includes("sort-field");
  const showSortDirection = parts.includes("sort-direction");
  const showViewModes = parts.includes("view-modes");
  const showSortGroup = showSortField || showSortDirection;

  if (!showSortField && !showSortDirection && !showViewModes) return null;

  return (
    <div
      className={`tm-processo-list-presentation${
        parts.length < ALL_PARTS.length ? " tm-processo-list-presentation--partial" : ""
      }`}
      aria-label="Ordenação e visualização"
    >
      {showSortGroup ? (
        <div className="tm-processo-list-presentation__sort" aria-label="Ordenação da lista">
          {showSortField ? (
            !departmentRoot ? (
              <SelectField
                id="tm-proc-sort-field"
                label="Ordenar por"
                hint={P.ordenacaoCampo}
                value={sort.key}
                onChange={(field) => onSortFieldChange(field as ProcessoListSortField)}
                options={PROCESSO_LIST_SORT_OPTIONS}
                className="tm-processo-list-presentation__sort-field"
              />
            ) : (
              <span className="tm-processo-list-presentation__sort-field-static">
                <FieldLabel className="tm-field__label" label="Ordenar por" hint={P.ordenacaoCampo} />
                <span className="ds-hint">Nome do departamento</span>
              </span>
            )
          ) : null}
          {showSortDirection ? (
            <div className="tm-processo-list-presentation__sort-direction">
              <FieldLabel
                className="tm-field__label tm-processo-list-presentation__sort-direction-label"
                label="Ordem"
                hint={P.ordenacaoDirecao}
              />
              <button
                type="button"
                className="tm-processo-list-presentation__sort-direction-btn"
                aria-label={`Ordem: ${sortDirectionLabel}. Clique para alternar.`}
                title={sortDirectionLabel}
                onClick={onToggleSortDirection}
              >
                {sort.direction === "asc" ? (
                  <ArrowDownAZ size={16} aria-hidden="true" />
                ) : (
                  <ArrowUpAZ size={16} aria-hidden="true" />
                )}
                <span>{sort.direction === "asc" ? "Menor" : "Maior"}</span>
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
      {showViewModes ? (
        <div
          className="tm-processo-list-presentation__view-modes"
          role="group"
          aria-label="Modo de visualização"
        >
          {PROCESSO_LIST_VIEW_MODES.map((mode) => {
            const Icon = viewModeIcon(mode.id);
            const active = viewMode === mode.id;
            return (
              <button
                key={mode.id}
                type="button"
                className={`tm-processo-list-presentation__view-btn${
                  active ? " tm-processo-list-presentation__view-btn--active" : ""
                }`}
                aria-pressed={active}
                title={mode.label}
                onClick={() => onViewModeChange(mode.id)}
              >
                <Icon size={16} aria-hidden="true" />
                <span>{mode.shortLabel}</span>
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
