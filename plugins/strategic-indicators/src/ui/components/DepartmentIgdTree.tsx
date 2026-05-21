import {
  useCallback,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import type {
  DepartmentTreeColumn,
  DepartmentTreeDepartmentNode,
  DepartmentTreeModel,
  DepartmentTreeScopeConfig,
} from "../../data/types/departmentTree";
import type { StrategicIndicatorsFilterState } from "../shared/strategicIndicatorsFilterUrl";
import { appendStrategicIndicatorsFiltersToPath } from "../shared/strategicIndicatorsFilterUrl";
import {
  formatIndicatorScore,
  formatScopeAwareMetric,
} from "../shared/indicatorValueFormatter";
import {
  getScoreStatusVariant,
  type ScoreStatusVariant,
} from "../shared/scoreVariant";
import { PanZoomCanvas } from "./PanZoomCanvas";
import "./DepartmentIgdTree.css";

type DepartmentIgdTreeProps = {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  isMultiColumn: boolean;
};

type OrgNodeTone =
  | "igd"
  | "scope"
  | "empty"
  | ScoreStatusVariant;

function buildDepartmentDetailHref(
  departmentId: string,
  scope: DepartmentTreeScopeConfig,
  filterState: StrategicIndicatorsFilterState,
) {
  const nextFilters: StrategicIndicatorsFilterState = scope.branch
    ? { ...filterState, viewMode: "branch", branch: scope.branch }
    : filterState;

  return appendStrategicIndicatorsFiltersToPath(
    `/apps/strategic-indicators/departments/${departmentId}`,
    nextFilters,
  );
}

function OrgChartArrow() {
  return (
    <div className="si-org-chart__arrow" aria-hidden="true">
      <span className="si-org-chart__arrow-stem" />
      <span className="si-org-chart__arrow-head" />
    </div>
  );
}

function OrgChartNode({
  title,
  subtitle,
  meta,
  tone,
  href,
  action,
  compact = false,
}: {
  title: string;
  subtitle?: string;
  meta?: string;
  tone: OrgNodeTone;
  href?: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  const className = [
    "si-org-chart__node",
    `si-org-chart__node--${tone}`,
    compact ? "si-org-chart__node--compact" : "",
    href ? "si-org-chart__node--link" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const content = (
    <>
      <strong className="si-org-chart__node-title">{title}</strong>
      {subtitle ? (
        <span className="si-org-chart__node-subtitle">{subtitle}</span>
      ) : null}
      {meta ? <span className="si-org-chart__node-meta">{meta}</span> : null}
      {action ? <div className="si-org-chart__node-action">{action}</div> : null}
    </>
  );

  if (href) {
    return (
      <a href={href} className={className}>
        {content}
      </a>
    );
  }

  return <div className={className}>{content}</div>;
}

function DepartmentOrgNode({
  node,
  scope,
  filterState,
  expanded,
  onToggle,
}: {
  node: DepartmentTreeDepartmentNode | null;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  expanded: boolean;
  onToggle: () => void;
}) {
  if (!node) {
    return (
      <OrgChartNode
        title="Sem medição"
        subtitle={scope.label}
        tone="empty"
      />
    );
  }

  const { department } = node;
  const tone = getScoreStatusVariant(department.score);
  const indicatorCount = node.indicators.length;

  return (
    <div className="si-org-chart__dept-stack">
      <OrgChartNode
        title={department.name}
        subtitle={`IDD ${department.score.toFixed(1)}`}
        meta={department.classification}
        tone={tone}
        action={
          <>
            <a
              href={buildDepartmentDetailHref(
                department.id,
                scope,
                filterState,
              )}
              className="si-org-chart__node-link"
            >
              Ver detalhe
            </a>
            {indicatorCount > 0 ? (
              <button
                type="button"
                className="si-org-chart__node-btn"
                onClick={onToggle}
                aria-expanded={expanded}
              >
                {expanded
                  ? "Recolher"
                  : `Indicadores (${indicatorCount})`}
              </button>
            ) : null}
          </>
        }
      />

      {expanded && indicatorCount > 0 ? (
        <>
          <OrgChartArrow />
          <div className="si-org-chart__indicator-row">
            {node.indicators.map((indicatorNode) => {
              const { indicator } = indicatorNode;
              const indicatorTone = indicator.hasValue
                ? getScoreStatusVariant(indicator.score ?? 0)
                : "empty";

              return (
                <OrgChartNode
                  key={indicator.id}
                  compact
                  title={indicator.name}
                  subtitle={
                    indicator.hasValue
                      ? formatIndicatorScore(indicator.score)
                      : "Sem nota"
                  }
                  meta={formatScopeAwareMetric(
                    indicator.realized,
                    {
                      valueUnit: indicator.valueUnit,
                      valuePrefix: indicator.valuePrefix,
                      valueSuffix: indicator.valueSuffix,
                      valueDecimals: indicator.valueDecimals,
                    },
                    { fallback: "—" },
                  )}
                  tone={indicatorTone}
                />
              );
            })}
          </div>
        </>
      ) : null}
    </div>
  );
}

function resolveDepartmentLabel(
  departmentId: string,
  columns: DepartmentTreeColumn[],
): string {
  for (const column of columns) {
    const node = column.departments.find(
      (item) => item.department.id === departmentId,
    );
    if (node) {
      return node.department.name;
    }
  }
  return "Departamento";
}

export function DepartmentIgdTree({
  model,
  filterState,
  isMultiColumn,
}: DepartmentIgdTreeProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());

  const columnCount = model.columns.length;

  const columnsByScope = useMemo(
    () =>
      model.columns.map((column) => ({
        column,
        nodesById: new Map(
          column.departments.map((item) => [item.department.id, item]),
        ),
      })),
    [model.columns],
  );

  const allExpandableKeys = useMemo(() => {
    const keys: string[] = [];

    for (const { column, nodesById } of columnsByScope) {
      for (const departmentId of model.departmentOrder) {
        const node = nodesById.get(departmentId);
        if (node && node.indicators.length > 0) {
          keys.push(`${column.scope.key}:${departmentId}`);
        }
      }
    }

    return keys;
  }, [columnsByScope, model.departmentOrder]);

  const toggleDepartment = useCallback((key: string) => {
    setExpandedKeys((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const expandAll = useCallback(() => {
    setExpandedKeys(new Set(allExpandableKeys));
  }, [allExpandableKeys]);

  const collapseAll = useCallback(() => {
    setExpandedKeys(new Set());
  }, []);

  const hasExpandable = allExpandableKeys.length > 0;

  const fitToken = `${model.competence}-${columnCount}-${model.departmentOrder.join("|")}`;

  const toolbar = (
    <>
      <span className="si-org-chart__toolbar-hint">
        Mapa Delpi · IGD → Visão → Departamentos → Indicadores
      </span>
      {hasExpandable ? (
        <div className="si-org-chart__toolbar-actions">
          <button
            type="button"
            className="si-org-chart__toolbar-btn"
            onClick={expandAll}
          >
            Expandir todos
          </button>
          <button
            type="button"
            className="si-org-chart__toolbar-btn"
            onClick={collapseAll}
          >
            Recolher todos
          </button>
        </div>
      ) : null}
    </>
  );

  return (
    <PanZoomCanvas fitToken={fitToken} toolbar={toolbar}>
      <div
        className="si-org-chart"
        style={
          { "--si-org-chart-cols": String(columnCount) } as CSSProperties
        }
      >
      <section className="si-org-chart__level si-org-chart__level--igd">
        <span className="si-org-chart__level-tag">Nível 1</span>
        <OrgChartNode
          title="IGD"
          subtitle="Grupo Delpi"
          meta={
            model.igd !== null
              ? `${model.igd.toFixed(1)} · ${model.classification ?? ""}`
              : "—"
          }
          tone="igd"
        />
        <p className="si-org-chart__competence">
          Competência {model.competence}
        </p>
      </section>

      <OrgChartArrow />

      <section className="si-org-chart__level">
        <span className="si-org-chart__level-tag">Nível 2 · Visão</span>
        <div className="si-org-chart__fork-row">
          {model.columns.map((column) => (
            <div key={column.scope.key} className="si-org-chart__fork-item">
              <OrgChartNode
                title="Visão"
                subtitle={column.scope.label}
                meta={
                  column.averageScore !== null
                    ? `Média IDD ${column.averageScore.toFixed(1)}`
                    : undefined
                }
                tone="scope"
              />
            </div>
          ))}
        </div>
      </section>

      <OrgChartArrow />

      <section className="si-org-chart__level si-org-chart__level--departments">
        <span className="si-org-chart__level-tag">Nível 3 · Departamentos</span>

        <div className="si-org-chart__department-blocks">
          {model.departmentOrder.map((departmentId) => (
            <div
              key={departmentId}
              className="si-org-chart__department-block"
            >
              {isMultiColumn ? (
                <p className="si-org-chart__department-anchor">
                  {resolveDepartmentLabel(departmentId, model.columns)}
                </p>
              ) : null}

              <div className="si-org-chart__fork-row">
                {columnsByScope.map(({ column, nodesById }) => {
                  const expandKey = `${column.scope.key}:${departmentId}`;
                  const node = nodesById.get(departmentId) ?? null;

                  return (
                    <div
                      key={expandKey}
                      className="si-org-chart__fork-item"
                    >
                      <DepartmentOrgNode
                        node={node}
                        scope={column.scope}
                        filterState={filterState}
                        expanded={expandedKeys.has(expandKey)}
                        onToggle={() => toggleDepartment(expandKey)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>
      </div>
    </PanZoomCanvas>
  );
}
