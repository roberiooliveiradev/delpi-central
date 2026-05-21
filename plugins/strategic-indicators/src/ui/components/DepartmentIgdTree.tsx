import { useCallback, useMemo, useState } from "react";
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
}: {
  node: DepartmentTreeDepartmentNode;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  expanded: boolean;
  onToggle: () => void;
}) {
  const { department } = node;
  const variationValue = department.variation.value;
  const variationPrefix = variationValue > 0 ? "+" : "";
  const indicatorCount = node.indicators.length;

  return (
    <article className="si-dept-tree__department">
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

function DepartmentTreeColumnPanel({
  column,
  departmentOrder,
  filterState,
  expandedKeys,
  onToggleDepartment,
}: {
  column: DepartmentTreeColumn;
  departmentOrder: string[];
  filterState: StrategicIndicatorsFilterState;
  expandedKeys: Set<string>;
  onToggleDepartment: (key: string) => void;
}) {
  const nodesById = useMemo(
    () => new Map(column.departments.map((item) => [item.department.id, item])),
    [column.departments],
  );

  return (
    <section className="si-dept-tree__column">
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

      <div className="si-dept-tree__column-body">
        {departmentOrder.map((departmentId) => {
          const node = nodesById.get(departmentId);
          const expandKey = `${column.scope.key}:${departmentId}`;

          if (!node) {
            return (
              <div
                key={expandKey}
                className="si-dept-tree__department si-dept-tree__department--empty"
              >
                <strong>Sem medição</strong>
                <p>Departamento sem dados neste escopo no período.</p>
              </div>
            );
          }

          return (
            <DepartmentTreeDepartmentCard
              key={expandKey}
              node={node}
              scope={column.scope}
              filterState={filterState}
              expanded={expandedKeys.has(expandKey)}
              onToggle={() => onToggleDepartment(expandKey)}
            />
          );
        })}

        {!column.hasData && departmentOrder.length === 0 ? (
          <div className="si-dept-tree__department si-dept-tree__department--empty">
            <strong>Sem medição</strong>
            <p>Nenhum departamento retornou dados para este escopo.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function DepartmentIgdTree({
  model,
  filterState,
  isMultiColumn,
}: DepartmentIgdTreeProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());

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

  const columnsClass = isMultiColumn
    ? "si-dept-tree__columns si-dept-tree__columns--multi"
    : "si-dept-tree__columns";

  return (
    <div className="si-dept-tree">
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
          Competência {model.competence}. A árvore abaixo detalha departamentos
          {isMultiColumn
            ? " em Consolidado, Filial 01 e Filial 02."
            : " na filial selecionada."}
        </p>
      </div>

      <div className="si-dept-tree__connector" aria-hidden="true" />

      <div className={columnsClass}>
        {model.columns.map((column: DepartmentTreeColumn) => (
          <DepartmentTreeColumnPanel
            key={column.scope.key}
            column={column}
            departmentOrder={model.departmentOrder}
            filterState={filterState}
            expandedKeys={expandedKeys}
            onToggleDepartment={toggleDepartment}
          />
        ))}
      </div>
    </div>
  );
}
