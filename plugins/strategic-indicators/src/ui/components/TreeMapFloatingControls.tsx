import { useCallback, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { DepartmentTreeScopeKey } from "../../data/types/departmentTree";
import { StrategicIndicatorsReferenceFilters } from "./StrategicIndicatorsReferenceFilters";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import "./TreeMapFloatingControls.css";

const FILTERS_COLLAPSED_KEY = "delpi.si.tree.filtersCollapsed";

type TreeMapFloatingControlsProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  treeScope: DepartmentTreeScopeKey;
  monthsToCompare: number;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onTreeScopeChange: (scope: DepartmentTreeScopeKey) => void;
  onMonthsToCompareChange: (value: number) => void;
  viewportNav?: ReactNode;
  actions?: ReactNode;
  headerActions?: ReactNode;
  status?: ReactNode;
};

function readFiltersCollapsedPreference() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.sessionStorage.getItem(FILTERS_COLLAPSED_KEY) === "1";
}

export function TreeMapFloatingControls({
  referenceMonth,
  viewMode,
  branch,
  treeScope,
  monthsToCompare,
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
  onTreeScopeChange,
  onMonthsToCompareChange,
  viewportNav,
  actions,
  headerActions,
  status,
}: TreeMapFloatingControlsProps) {
  const [collapsed, setCollapsed] = useState(readFiltersCollapsedPreference);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((current) => {
      const next = !current;
      if (typeof window !== "undefined") {
        window.sessionStorage.setItem(FILTERS_COLLAPSED_KEY, next ? "1" : "0");
      }
      return next;
    });
  }, []);

  return (
    <div
      className={`si-tree-map-floating${
        collapsed ? " si-tree-map-floating--collapsed" : ""
      }`}
      data-pan-zoom-lock="true"
    >
      <div
        className={`si-tree-map-floating__panel${
          collapsed ? " si-tree-map-floating__panel--collapsed" : ""
        }`}
      >
        <div className="si-tree-map-floating__toolbar">
          <div className="si-tree-map-floating__row si-tree-map-floating__row--head">
            <button
              type="button"
              className={`si-tree-map-floating__toggle${
                collapsed ? " si-tree-map-floating__toggle--compact" : ""
              }`}
              onClick={toggleCollapsed}
              aria-expanded={!collapsed}
              title={collapsed ? "Mostrar filtros" : "Ocultar filtros"}
            >
              {collapsed ? (
                <>
                  <ChevronDown size={16} aria-hidden />
                  <span>Filtros</span>
                </>
              ) : (
                <>
                  <ChevronUp size={16} aria-hidden />
                  <span>Ocultar filtros</span>
                </>
              )}
            </button>

            {!collapsed && (status || headerActions) ? (
              <div className="si-tree-map-floating__head-trail">
                {status ? (
                  <div className="si-tree-map-floating__status">{status}</div>
                ) : null}
                {headerActions ? (
                  <div className="si-tree-map-floating__header-actions">
                    {headerActions}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>

          {!collapsed ? (
            <div className="si-tree-map-floating__row si-tree-map-floating__row--filters">
              <StrategicIndicatorsReferenceFilters
                referenceMonth={referenceMonth}
                viewMode={viewMode}
                branch={branch}
                treeScope={treeScope}
                monthsToCompare={monthsToCompare}
                showMonthsToCompare
                viewPickerVariant="tree"
                onReferenceMonthChange={onReferenceMonthChange}
                onViewModeChange={onViewModeChange}
                onBranchChange={onBranchChange}
                onTreeScopeChange={onTreeScopeChange}
                onMonthsToCompareChange={onMonthsToCompareChange}
                className="si-tree-map-floating__filters"
              />
            </div>
          ) : null}

          {actions || viewportNav ? (
            <div className="si-tree-map-floating__row si-tree-map-floating__row--viewport">
              <div
                className="si-tree-map-floating__view-controls"
                aria-label="Controles de visualização"
              >
                {actions ? (
                  <div className="si-tree-map-floating__tree-actions">{actions}</div>
                ) : null}
                {viewportNav ? (
                  <div className="si-tree-map-floating__nav">{viewportNav}</div>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
