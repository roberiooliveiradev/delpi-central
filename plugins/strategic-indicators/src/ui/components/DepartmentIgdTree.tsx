import { useCallback, useMemo, useState, type CSSProperties } from "react";
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
  isMissingValueClassification,
} from "../shared/indicatorValueFormatter";
import { getScoreStatusVariant } from "../shared/scoreVariant";
import { StatusBadge } from "./StatusBadge";
import "./DepartmentIgdTree.css";

type DepartmentIgdTreeProps = {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  isMultiColumn: boolean;
};

function getDirectionLabel(direction: string) {
  if (direction === "up") return "Alta";
  if (direction === "down") return "Queda";
  return "Estável";
}

function buildDepartmentDetailHref(
  departmentId: string,
  scope: DepartmentTreeScopeConfig,
  filterState: StrategicIndicatorsFilterState,
) {
  const nextFilters: StrategicIndicatorsFilterState = scope.branch
    ? {
        ...filterState,
        viewMode: "branch",
        branch: scope.branch,
      }
    : filterState;

  return appendStrategicIndicatorsFiltersToPath(
    `/apps/strategic-indicators/departments/${departmentId}`,
    nextFilters,
  );
}

function DepartmentTreeIndicatorRow({
  node,
}: {
  node: DepartmentTreeDepartmentNode["indicators"][number];
}) {
  const { indicator } = node;
  const format = {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };

  return (
    <li className="si-dept-tree__indicator">
      <div className="si-dept-tree__indicator-head">
        <strong>{indicator.name}</strong>
        <span>{indicator.weightPct}%</span>
      </div>
      <div className="si-dept-tree__indicator-meta">
        <span>
          Nota:{" "}
          <strong>
            {indicator.hasValue
              ? formatIndicatorScore(indicator.score)
              : "—"}
          </strong>
        </span>
        <span>
          Realizado:{" "}
          <strong>
            {formatScopeAwareMetric(indicator.realized, format, {
              fallback: "—",
            })}
          </strong>
        </span>
      </div>
      {!isMissingValueClassification(indicator.classification) ? (
        <StatusBadge label={indicator.classification} variant="neutral" />
      ) : null}
    </li>
  );
}

function DepartmentTreeDepartmentCard({
  node,
  scope,
  filterState,
  expanded,
  onToggle,
  showDepartmentTitle = true,
}: {
  node: DepartmentTreeDepartmentNode | null;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  expanded: boolean;
  onToggle: () => void;
  showDepartmentTitle?: boolean;
}) {
  if (!node) {
    return (
      <article className="si-dept-tree__department si-dept-tree__department--empty">
        <strong>Sem medição</strong>
        <p>Departamento sem dados neste escopo no período.</p>
      </article>
    );
  }

  const { department } = node;
  const variationValue = department.variation.value;
  const variationPrefix = variationValue > 0 ? "+" : "";
  const indicatorCount = node.indicators.length;

  return (
    <article className="si-dept-tree__department">
      {showDepartmentTitle ? (
        <div className="si-dept-tree__department-head">
          <div>
            <strong>{department.name}</strong>
            <p>{department.strategicSummary}</p>
          </div>
          <StatusBadge
            label={department.classification}
            variant={getScoreStatusVariant(department.score)}
          />
        </div>
      ) : (
        <div className="si-dept-tree__department-head si-dept-tree__department-head--compact">
          <StatusBadge
            label={department.classification}
            variant={getScoreStatusVariant(department.score)}
          />
        </div>
      )}

      <dl className="si-dept-tree__department-metrics">
        <div>
          <dt>Peso no IGD</dt>
          <dd>{department.weightInIgd}%</dd>
        </div>
        <div>
          <dt>IDD</dt>
          <dd>{department.score.toFixed(1)}</dd>
        </div>
        <div>
          <dt>Variação</dt>
          <dd>
            {variationPrefix}
            {variationValue.toFixed(1)} ·{" "}
            {getDirectionLabel(department.variation.direction)}
          </dd>
        </div>
      </dl>

      <div className="si-dept-tree__department-actions">
        {indicatorCount > 0 ? (
          <button
            type="button"
            className="si-dept-tree__toggle"
            onClick={onToggle}
            aria-expanded={expanded}
          >
            {expanded ? "Recolher indicadores" : `Indicadores (${indicatorCount})`}
          </button>
        ) : null}
        <a
          href={buildDepartmentDetailHref(department.id, scope, filterState)}
          className="si-link-button"
        >
          Ver detalhe
        </a>
      </div>

      {expanded && indicatorCount > 0 ? (
        <ul className="si-dept-tree__indicator-list">
          {node.indicators.map((indicatorNode) => (
            <DepartmentTreeIndicatorRow
              key={indicatorNode.indicator.id}
              node={indicatorNode}
            />
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function DepartmentTreeScopeHeader({ column }: { column: DepartmentTreeColumn }) {
  return (
    <header className="si-dept-tree__column-head">
      <div>
        <span className="si-dept-tree__column-eyebrow">Escopo</span>
        <strong>{column.scope.label}</strong>
      </div>
      {column.averageScore !== null ? (
        <div className="si-dept-tree__column-score">
          <span>Média IDD</span>
          <strong>{column.averageScore.toFixed(1)}</strong>
        </div>
      ) : null}
    </header>
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

function resolveDepartmentSummary(
  departmentId: string,
  columns: DepartmentTreeColumn[],
): string | null {
  for (const column of columns) {
    const node = column.departments.find(
      (item) => item.department.id === departmentId,
    );
    if (node) {
      return node.department.strategicSummary;
    }
  }
  return null;
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

  const selectedViewLabel = isMultiColumn
    ? "Consolidado · Filial 01 · Filial 02"
    : (model.columns[0]?.scope.label ?? "Filial");

  const hasExpandable = allExpandableKeys.length > 0;

  return (
    <div
      className="si-dept-tree"
      style={
        { "--si-dept-tree-cols": String(columnCount) } as CSSProperties
      }
    >
      <section className="si-dept-tree__level si-dept-tree__level--root">
        <div className="si-dept-tree__root">
          <span className="si-dept-tree__root-eyebrow">Grupo Delpi</span>
          <strong className="si-dept-tree__root-title">IGD consolidado</strong>
          <div className="si-dept-tree__root-metrics">
            <div>
              <span>IGD</span>
              <strong>
                {model.igd !== null ? model.igd.toFixed(1) : "—"}
              </strong>
            </div>
            {model.classification ? (
              <StatusBadge
                label={model.classification}
                variant={
                  model.igd !== null
                    ? getScoreStatusVariant(model.igd)
                    : "neutral"
                }
              />
            ) : null}
          </div>
          <p className="si-dept-tree__root-note">
            Competência {model.competence}.
          </p>
        </div>
      </section>

      <div className="si-dept-tree__connector" aria-hidden="true" />

      <section className="si-dept-tree__level si-dept-tree__level--scopes">
        <p className="si-dept-tree__level-label">
          Visão analítica: <strong>{selectedViewLabel}</strong>
        </p>

        <div className="si-dept-tree__toolbar">
          <span className="si-dept-tree__toolbar-hint">
            Departamentos alinhados por linha entre os escopos.
          </span>
          {hasExpandable ? (
            <div className="si-dept-tree__toolbar-actions">
              <button
                type="button"
                className="si-dept-tree__toolbar-btn"
                onClick={expandAll}
              >
                Expandir todos
              </button>
              <button
                type="button"
                className="si-dept-tree__toolbar-btn"
                onClick={collapseAll}
              >
                Recolher todos
              </button>
            </div>
          ) : null}
        </div>

        <div className="si-dept-tree__scope-headers">
          {model.columns.map((column) => (
            <DepartmentTreeScopeHeader key={column.scope.key} column={column} />
          ))}
        </div>

        <div className="si-dept-tree__department-rows">
          {model.departmentOrder.map((departmentId) => {
            const departmentName = resolveDepartmentLabel(
              departmentId,
              model.columns,
            );
            const departmentSummary = resolveDepartmentSummary(
              departmentId,
              model.columns,
            );

            return (
              <div key={departmentId} className="si-dept-tree__department-row">
                <div className="si-dept-tree__department-row-title">
                  <strong>{departmentName}</strong>
                  {departmentSummary ? <span>{departmentSummary}</span> : null}
                </div>

                <div className="si-dept-tree__department-row-cells">
                  {columnsByScope.map(({ column, nodesById }) => {
                    const expandKey = `${column.scope.key}:${departmentId}`;
                    const node = nodesById.get(departmentId) ?? null;

                    return (
                      <div
                        key={expandKey}
                        className="si-dept-tree__department-row-cell"
                      >
                        <DepartmentTreeDepartmentCard
                          node={node}
                          scope={column.scope}
                          filterState={filterState}
                          expanded={expandedKeys.has(expandKey)}
                          onToggle={() => toggleDepartment(expandKey)}
                          showDepartmentTitle={!isMultiColumn}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
