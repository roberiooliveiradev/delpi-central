import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { ChevronDown } from "lucide-react";
import type { IndicatorViewItem } from "../../data/types/indicators";
import type {
  DepartmentTreeColumn,
  DepartmentTreeDepartmentNode,
  DepartmentTreeModel,
  DepartmentTreeScopeConfig,
} from "../../data/types/departmentTree";
import type { StrategicIndicatorsFilterState } from "../shared/strategicIndicatorsFilterUrl";
import { appendStrategicIndicatorsFiltersToPath } from "../shared/strategicIndicatorsFilterUrl";
import {
  formatIndicatorGapDisplay,
  formatIndicatorGoalValue,
  formatIndicatorRealizedDisplay,
  formatIndicatorScore,
  isMissingValueClassification,
} from "../shared/indicatorValueFormatter";
import {
  getScoreStatusVariant,
  type ScoreStatusVariant,
} from "../shared/scoreVariant";
import { getScopeTypeLabel } from "../presentation/labels";
import { StatusBadge } from "./StatusBadge";
import { PanZoomCanvas } from "./PanZoomCanvas";
import "./DepartmentIgdTree.css";

type DepartmentIgdTreeProps = {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  isMultiColumn: boolean;
};

type OrgNodeTone = "igd" | "scope" | "empty" | ScoreStatusVariant;

function getDirectionLabel(direction: string) {
  if (direction === "up") return "Alta";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getTrendLabel(direction: string) {
  if (direction === "up") return "↑ Alta";
  if (direction === "down") return "↓ Queda";
  return "→ Estável";
}

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

function getIndicatorValueFormat(indicator: IndicatorViewItem) {
  return {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };
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
}: {
  title: string;
  subtitle?: string;
  meta?: string;
  tone: OrgNodeTone;
}) {
  return (
    <div className={`si-org-chart__node si-org-chart__node--${tone}`}>
      <strong className="si-org-chart__node-title">{title}</strong>
      {subtitle ? (
        <span className="si-org-chart__node-subtitle">{subtitle}</span>
      ) : null}
      {meta ? <span className="si-org-chart__node-meta">{meta}</span> : null}
    </div>
  );
}

function IndicatorTreeCard({
  indicator,
  competence,
}: {
  indicator: IndicatorViewItem;
  competence: string;
}) {
  const valueFormat = getIndicatorValueFormat(indicator);
  const tone = indicator.hasValue
    ? getScoreStatusVariant(indicator.score ?? 0)
    : "empty";

  return (
    <article
      className={`si-tree-indicator si-tree-indicator--${tone}`}
      data-pan-zoom-lock="true"
    >
      <header className="si-tree-indicator__head">
        <div className="si-tree-indicator__title-wrap">
          <strong className="si-tree-indicator__name">{indicator.name}</strong>
          <span className="si-tree-indicator__weight">
            Peso {indicator.weightPct}%
          </span>
        </div>
        {!isMissingValueClassification(indicator.classification) ? (
          <StatusBadge
            label={indicator.classification}
            variant={tone === "empty" ? "neutral" : tone}
          />
        ) : null}
      </header>

      <div className="si-tree-indicator__metrics">
        <div className="si-tree-indicator__metric">
          <span>Meta</span>
          <strong>{formatIndicatorGoalValue(indicator, competence)}</strong>
        </div>
        <div className="si-tree-indicator__metric">
          <span>Realizado</span>
          <strong>
            {formatIndicatorRealizedDisplay(indicator, valueFormat)}
          </strong>
        </div>
        <div className="si-tree-indicator__metric">
          <span>Nota</span>
          <strong
            className={
              !indicator.hasValue ? "si-tree-indicator__value--missing" : ""
            }
          >
            {formatIndicatorScore(indicator.score)}
          </strong>
        </div>
        <div className="si-tree-indicator__metric">
          <span>Gap</span>
          <strong
            className={
              !indicator.hasValue ? "si-tree-indicator__value--missing" : ""
            }
          >
            {formatIndicatorGapDisplay(indicator, valueFormat)}
          </strong>
        </div>
        <div className="si-tree-indicator__metric">
          <span>Tendência</span>
          <strong>{getTrendLabel(indicator.trend)}</strong>
        </div>
        <div className="si-tree-indicator__metric">
          <span>Escopo</span>
          <strong>{getScopeTypeLabel(indicator.scopeType)}</strong>
        </div>
      </div>
    </article>
  );
}

function DepartmentTreeCard({
  node,
  scope,
  filterState,
  competence,
  expanded,
  onToggle,
  showDepartmentTitle,
}: {
  node: DepartmentTreeDepartmentNode | null;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  competence: string;
  expanded: boolean;
  onToggle: () => void;
  showDepartmentTitle: boolean;
}) {
  if (!node) {
    return (
      <article className="si-tree-dept si-tree-dept--empty">
        <strong>Sem medição</strong>
        <p>Sem dados em {scope.label} no período.</p>
      </article>
    );
  }

  const { department } = node;
  const tone = getScoreStatusVariant(department.score);
  const variationValue = department.variation.value;
  const variationPrefix = variationValue > 0 ? "+" : "";
  const indicatorCount = node.indicators.length;

  return (
    <article className={`si-tree-dept si-tree-dept--${tone}`}>
      <header className="si-tree-dept__head">
        <div className="si-tree-dept__identity">
          {showDepartmentTitle ? (
            <>
              <strong className="si-tree-dept__name">{department.name}</strong>
              <p className="si-tree-dept__summary">
                {department.strategicSummary}
              </p>
            </>
          ) : null}
          <div className="si-tree-dept__score-row">
            <span className="si-tree-dept__idd">
              IDD <em>{department.score.toFixed(1)}</em>
            </span>
            <StatusBadge
              label={department.classification}
              variant={tone}
            />
          </div>
        </div>
      </header>

      <dl className="si-tree-dept__stats">
        <div>
          <dt>Peso no IGD</dt>
          <dd>{department.weightInIgd}%</dd>
        </div>
        <div>
          <dt>Variação</dt>
          <dd>
            {variationPrefix}
            {variationValue.toFixed(1)} ·{" "}
            {getDirectionLabel(department.variation.direction)}
          </dd>
        </div>
        <div>
          <dt>Escopo</dt>
          <dd>{scope.label}</dd>
        </div>
      </dl>

      <div className="si-tree-dept__actions" data-pan-zoom-lock="true">
        <a
          href={buildDepartmentDetailHref(
            department.id,
            scope,
            filterState,
          )}
          className="si-tree-dept__link si-link-button"
        >
          Ver detalhe do departamento
        </a>
        {indicatorCount > 0 ? (
          <button
            type="button"
            className="si-tree-dept__toggle"
            onClick={onToggle}
            aria-expanded={expanded}
          >
            <span>Nível 4 · Indicadores ({indicatorCount})</span>
            <ChevronDown
              size={16}
              className={
                expanded ? "si-tree-dept__chevron--open" : undefined
              }
              aria-hidden
            />
          </button>
        ) : (
          <span className="si-tree-dept__no-indicators">
            Nenhum indicador neste escopo
          </span>
        )}
      </div>

      {expanded && indicatorCount > 0 ? (
        <section className="si-tree-dept__indicators">
          <OrgChartArrow />
          <div className="si-tree-dept__indicator-list">
            {node.indicators.map((indicatorNode) => (
              <IndicatorTreeCard
                key={indicatorNode.indicator.id}
                indicator={indicatorNode.indicator}
                competence={competence}
              />
            ))}
          </div>
        </section>
      ) : null}
    </article>
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

  useEffect(() => {
    setExpandedKeys(new Set(allExpandableKeys));
  }, [allExpandableKeys]);

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

  const toolbar: ReactNode = (
    <>
      <span className="si-org-chart__toolbar-hint">
        Mapa Delpi · dados completos por indicador (meta, realizado, nota e gap)
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
          <span className="si-org-chart__level-tag">
            Nível 3 · Departamentos · Nível 4 · Indicadores
          </span>

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
                        <DepartmentTreeCard
                          node={node}
                          scope={column.scope}
                          filterState={filterState}
                          competence={model.competence}
                          expanded={expandedKeys.has(expandKey)}
                          onToggle={() => toggleDepartment(expandKey)}
                          showDepartmentTitle={!isMultiColumn}
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
