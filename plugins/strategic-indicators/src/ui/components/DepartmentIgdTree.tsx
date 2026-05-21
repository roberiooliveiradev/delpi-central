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
  DepartmentTreeIndicatorNode,
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
import { getScopeTypeLabel } from "../presentation/labels";
import { StatusBadge } from "./StatusBadge";
import { PanZoomCanvas } from "./PanZoomCanvas";
import { TreeMapFloatingControls } from "./TreeMapFloatingControls";
import { TreeSparkline } from "./TreeSparkline";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import "./DepartmentSummaryCard.css";
import "./IndicatorDetailCard.css";
import "./IgdHeroCard.css";
import "./TrendHeroCard.css";
import "./DepartmentIgdTree.css";

type DepartmentIgdTreeFilterControls = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  monthsToCompare: number;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onMonthsToCompareChange: (value: number) => void;
  status?: ReactNode;
};

type DepartmentIgdTreeProps = {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  isMultiColumn: boolean;
  filterControls: DepartmentIgdTreeFilterControls;
};

function mapScoreToBadgeVariant(
  score: number,
): "success" | "info" | "warning" | "danger" {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}

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

function buildTrendsHref(
  filterState: StrategicIndicatorsFilterState,
  scope: DepartmentTreeScopeConfig,
) {
  const nextFilters: StrategicIndicatorsFilterState = scope.branch
    ? { ...filterState, viewMode: "branch", branch: scope.branch }
    : filterState;

  return appendStrategicIndicatorsFiltersToPath(
    "/apps/strategic-indicators/trends",
    nextFilters,
  );
}

function TreeIgdCard({
  model,
  filterState,
  cardId,
  isActive,
  onActivate,
}: {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  cardId: string;
  isActive: boolean;
  onActivate: (cardId: string) => void;
}) {
  const badgeVariant =
    model.igd !== null
      ? mapScoreToBadgeVariant(model.igd)
      : ("neutral" as const);

  return (
    <InteractiveTreeCard
      href={appendStrategicIndicatorsFiltersToPath(
        "/apps/strategic-indicators",
        filterState,
      )}
      cardId={cardId}
      isActive={isActive}
      onActivate={onActivate}
      className="si-tree-igd-card__link"
    >
      <section className="si-igd-hero si-igd-hero--tree">
        <p className="si-igd-hero__eyebrow">Índice Global Delpi</p>
        <div className="si-igd-hero__headline">
          <div>
            <h2 className="si-igd-hero__value">
              {model.igd !== null ? model.igd.toFixed(1) : "—"}
            </h2>
            <p className="si-igd-hero__exact">Competência {model.competence}</p>
          </div>
          {model.classification ? (
            <StatusBadge label={model.classification} variant={badgeVariant} />
          ) : null}
        </div>
        {model.igdSeries.length > 0 ? (
          <TreeSparkline
            points={model.igdSeries}
            direction="stable"
            height={48}
            label="Evolução · últimos meses"
          />
        ) : null}
      </section>
    </InteractiveTreeCard>
  );
}

function TreeScopeCard({
  column,
  filterState,
  cardId,
  isActive,
  onActivate,
}: {
  column: DepartmentTreeColumn;
  filterState: StrategicIndicatorsFilterState;
  cardId: string;
  isActive: boolean;
  onActivate: (cardId: string) => void;
}) {
  const score = column.averageScore;
  const badgeVariant =
    score !== null ? mapScoreToBadgeVariant(score) : ("neutral" as const);

  return (
    <InteractiveTreeCard
      href={buildTrendsHref(filterState, column.scope)}
      cardId={cardId}
      isActive={isActive}
      onActivate={onActivate}
      className="si-tree-scope-card__link"
    >
      <section className="si-trend-hero si-trend-hero--tree si-trend-hero--stable">
        <div className="si-trend-hero__glow" aria-hidden />
        <div className="si-trend-hero__header">
          <div className="si-trend-hero__headline">
            <p className="si-trend-hero__eyebrow">Visão analítica</p>
            <h2 className="si-trend-hero__value">
              {score !== null ? score.toFixed(1) : "—"}
            </h2>
            <p className="si-trend-hero__classification">{column.scope.label}</p>
          </div>
          <StatusBadge
            label={score !== null ? "Média IDD" : "Sem dado"}
            variant={badgeVariant}
          />
        </div>
        <p className="si-trend-hero__description">
          Média dos departamentos neste escopo. Clique para abrir tendências
          detalhadas.
        </p>
      </section>
    </InteractiveTreeCard>
  );
}

function InteractiveTreeCard({
  href,
  cardId,
  isActive,
  onActivate,
  className,
  children,
}: {
  href: string;
  cardId: string;
  isActive: boolean;
  onActivate: (cardId: string) => void;
  className: string;
  children: ReactNode;
}) {
  return (
    <a
      href={href}
      className={`${className} si-tree-card--interactive${
        isActive ? " si-tree-card--active" : ""
      }`}
      onMouseDown={() => onActivate(cardId)}
      onFocus={() => onActivate(cardId)}
    >
      {children}
    </a>
  );
}

function IndicatorTreeCard({
  indicatorNode,
  competence,
  href,
  cardId,
  isActive,
  onActivate,
}: {
  indicatorNode: DepartmentTreeIndicatorNode;
  competence: string;
  href: string;
  cardId: string;
  isActive: boolean;
  onActivate: (cardId: string) => void;
}) {
  const { indicator, series } = indicatorNode;
  const valueFormat = getIndicatorValueFormat(indicator);
  const badgeVariant = indicator.hasValue
    ? mapScoreToBadgeVariant(indicator.score ?? 0)
    : "neutral";

  return (
    <InteractiveTreeCard
      href={href}
      cardId={cardId}
      isActive={isActive}
      onActivate={onActivate}
      className="si-tree-indicator-card__link"
    >
      <article className="si-indicator-card si-tree-indicator-card">
        <div className="si-indicator-card__header">
          <h3 className="si-indicator-card__title">{indicator.name}</h3>
          <span className="si-indicator-card__weight">
            Peso {indicator.weightPct}%
          </span>
        </div>

        {series.length > 0 ? (
          <TreeSparkline
            points={series}
            direction={indicator.trend}
            height={44}
            label="Histórico · últimos meses"
          />
        ) : null}

        <div className="si-tree-indicator-card__goals">
          <div className="si-indicator-card__goal">
            <span className="si-indicator-card__goal-label">Meta</span>
            <strong className="si-indicator-card__goal-value">
              {formatIndicatorGoalValue(indicator, competence)}
            </strong>
          </div>
          <div className="si-indicator-card__goal">
            <span className="si-indicator-card__goal-label">Realizado</span>
            <strong
              className={`si-indicator-card__goal-value${
                !indicator.hasValue
                  ? " si-indicator-card__goal-value--missing"
                  : ""
              }`}
            >
              {formatIndicatorRealizedDisplay(indicator, valueFormat)}
            </strong>
          </div>
          <div className="si-indicator-card__goal">
            <span className="si-indicator-card__goal-label">Nota</span>
            <strong
              className={`si-indicator-card__goal-value${
                !indicator.hasValue
                  ? " si-indicator-card__goal-value--missing"
                  : ""
              }`}
            >
              {formatIndicatorScore(indicator.score)}
            </strong>
          </div>
          <div className="si-indicator-card__goal">
            <span className="si-indicator-card__goal-label">Gap</span>
            <strong
              className={`si-indicator-card__goal-value${
                !indicator.hasValue
                  ? " si-indicator-card__goal-value--missing"
                  : ""
              }`}
            >
              {formatIndicatorGapDisplay(indicator, valueFormat)}
            </strong>
          </div>
        </div>

        <div className="si-tree-indicator-card__footer">
          {!isMissingValueClassification(indicator.classification) ? (
            <StatusBadge
              label={indicator.classification}
              variant={badgeVariant}
            />
          ) : (
            <StatusBadge label="Sem dado" variant="neutral" />
          )}
          <span className="si-tree-indicator-card__meta">
            {getTrendLabel(indicator.trend)} ·{" "}
            {getScopeTypeLabel(indicator.scopeType)}
          </span>
        </div>
      </article>
    </InteractiveTreeCard>
  );
}

function getDepartmentCardVariant(
  score: number,
): "success" | "info" | "warning" | "danger" {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}

function DepartmentTreeCard({
  node,
  scope,
  filterState,
  competence,
  expanded,
  onToggle,
  showDepartmentHeader,
  activeCardId,
  onActivateCard,
}: {
  node: DepartmentTreeDepartmentNode | null;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  competence: string;
  expanded: boolean;
  onToggle: () => void;
  showDepartmentHeader: boolean;
  activeCardId: string | null;
  onActivateCard: (cardId: string) => void;
}) {
  if (!node) {
    return (
      <article className="si-department-card si-tree-dept-card si-tree-dept-card--empty">
        <strong>Sem medição</strong>
        <p>Sem dados em {scope.label} no período.</p>
      </article>
    );
  }

  const { department } = node;
  const cardVariant = getDepartmentCardVariant(department.score);
  const variationValue = department.variation.value;
  const variationPrefix = variationValue > 0 ? "+" : "";
  const indicatorCount = node.indicators.length;
  const keyIndicators = node.indicators
    .slice(0, 3)
    .map((item) => item.indicator.name);
  const detailHref = buildDepartmentDetailHref(
    department.id,
    scope,
    filterState,
  );
  const deptCardId = `dept:${scope.key}:${department.id}`;

  return (
    <article className="si-tree-dept-wrap">
      <InteractiveTreeCard
        href={detailHref}
        cardId={deptCardId}
        isActive={activeCardId === deptCardId}
        onActivate={onActivateCard}
        className="si-tree-dept-card__link"
      >
        <div className="si-department-card si-tree-dept-card">
          <div className="si-department-card__top">
            <div className="si-department-card__identity">
              {showDepartmentHeader ? (
                <>
                  <span className="si-department-card__short">
                    {department.shortName}
                  </span>
                  <div>
                    <h3 className="si-department-card__title">
                      {department.name}
                    </h3>
                    <p className="si-department-card__weight">
                      peso no IGD: {department.weightInIgd}%
                    </p>
                  </div>
                </>
              ) : (
                <div>
                  <h3 className="si-department-card__title">{scope.label}</h3>
                  <p className="si-department-card__weight">
                    {department.classification}
                  </p>
                </div>
              )}
            </div>

            <StatusBadge
              label={department.score.toFixed(1)}
              variant={cardVariant}
            />
          </div>

          {showDepartmentHeader ? (
            <p className="si-department-card__summary">
              {department.strategicSummary}
            </p>
          ) : null}

          <div className="si-department-card__goal">
            <span className="si-department-card__goal-label">
              {showDepartmentHeader ? "Referência executiva" : "Visão analítica"}
            </span>
            <strong className="si-department-card__goal-value">
              {department.classification}
              {!showDepartmentHeader ? ` · ${scope.label}` : null}
            </strong>
          </div>

          <div className="si-department-card__metrics">
            <div className="si-department-card__metric">
              <span className="si-department-card__metric-label">IDD</span>
              <strong className="si-department-card__metric-value">
                {department.score.toFixed(1)}
              </strong>
            </div>
            <div className="si-department-card__metric">
              <span className="si-department-card__metric-label">
                Contribuição
              </span>
              <strong className="si-department-card__metric-value">
                {department.contribution.toFixed(3)}
              </strong>
            </div>
          </div>

          <div className="si-tree-dept-card__trend">
            <span className="si-tree-dept-card__trend-label">
              Variação {variationPrefix}
              {variationValue.toFixed(1)} ·{" "}
              {getDirectionLabel(department.variation.direction)}
            </span>
            <TreeSparkline
              points={node.series}
              direction={department.variation.direction}
              height={44}
              label="IDD · 6 meses"
            />
          </div>

          {keyIndicators.length > 0 ? (
            <div className="si-department-card__indicators">
              <span className="si-department-card__indicators-label">
                Indicadores-chave
              </span>
              <ul className="si-department-card__indicator-list">
                {keyIndicators.map((indicator) => (
                  <li key={indicator}>{indicator}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <p className="si-tree-dept-card__cta">Ver detalhe do departamento</p>
        </div>
      </InteractiveTreeCard>

      <div className="si-tree-dept__actions" data-pan-zoom-lock="true">
        {indicatorCount > 0 ? (
          <button
            type="button"
            className="si-tree-dept__toggle"
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              onToggle();
            }}
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
        <section className="si-tree-dept__indicators" data-pan-zoom-lock="true">
          <OrgChartArrow />
          <div className="si-tree-dept__indicator-list">
            {node.indicators.map((indicatorNode) => {
              const indicatorCardId = `ind:${scope.key}:${department.id}:${indicatorNode.indicator.id}`;

              return (
                <IndicatorTreeCard
                  key={indicatorNode.indicator.id}
                  indicatorNode={indicatorNode}
                  competence={competence}
                  href={detailHref}
                  cardId={indicatorCardId}
                  isActive={activeCardId === indicatorCardId}
                  onActivate={onActivateCard}
                />
              );
            })}
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
  filterControls,
}: DepartmentIgdTreeProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

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

  const departmentCount = model.departmentOrder.length;

  const fitToken = `${model.competence}-${columnCount}-${model.departmentOrder.join("|")}`;

  const chartStyle = {
    "--si-org-chart-cols": String(columnCount),
    "--si-dept-count": String(departmentCount),
  } as CSSProperties;

  const mapActions = hasExpandable ? (
    <>
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
    </>
  ) : null;

  const floatingControls = (
    <TreeMapFloatingControls
      referenceMonth={filterControls.referenceMonth}
      viewMode={filterControls.viewMode}
      branch={filterControls.branch}
      monthsToCompare={filterControls.monthsToCompare}
      onReferenceMonthChange={filterControls.onReferenceMonthChange}
      onViewModeChange={filterControls.onViewModeChange}
      onBranchChange={filterControls.onBranchChange}
      onMonthsToCompareChange={filterControls.onMonthsToCompareChange}
      actions={mapActions}
      status={filterControls.status}
    />
  );

  return (
    <PanZoomCanvas
      fitToken={fitToken}
      immersive
      floatingControls={floatingControls}
      className="si-org-chart-canvas"
    >
      <div className="si-org-chart" style={chartStyle}>
        <section className="si-org-chart__level si-org-chart__level--igd">
          <span className="si-org-chart__level-tag">IGD</span>
          <TreeIgdCard
            model={model}
            filterState={filterState}
            cardId="igd:root"
            isActive={activeCardId === "igd:root"}
            onActivate={setActiveCardId}
          />
        </section>

        <OrgChartArrow />

        <section className="si-org-chart__level">
          <span className="si-org-chart__level-tag">Visão</span>
          <div className="si-org-chart__fork-row">
            {model.columns.map((column) => (
              <div key={column.scope.key} className="si-org-chart__fork-item">
                <TreeScopeCard
                  column={column}
                  filterState={filterState}
                  cardId={`scope:${column.scope.key}`}
                  isActive={activeCardId === `scope:${column.scope.key}`}
                  onActivate={setActiveCardId}
                />
              </div>
            ))}
          </div>
        </section>

        <OrgChartArrow />

        <section className="si-org-chart__level si-org-chart__level--departments">
          <span className="si-org-chart__level-tag">Departamentos e indicadores</span>

          <div className="si-org-chart__departments-row">
            {model.departmentOrder.map((departmentId) => (
              <div
                key={departmentId}
                className="si-org-chart__department-column"
              >
                {isMultiColumn ? (
                  <p className="si-org-chart__department-anchor">
                    {resolveDepartmentLabel(departmentId, model.columns)}
                  </p>
                ) : null}

                <div className="si-org-chart__department-scopes">
                  {columnsByScope.map(({ column, nodesById }) => {
                    const expandKey = `${column.scope.key}:${departmentId}`;
                    const node = nodesById.get(departmentId) ?? null;

                    return (
                      <div
                        key={expandKey}
                        className="si-org-chart__department-scope"
                      >
                        <DepartmentTreeCard
                          node={node}
                          scope={column.scope}
                          filterState={filterState}
                          competence={model.competence}
                          expanded={expandedKeys.has(expandKey)}
                          onToggle={() => toggleDepartment(expandKey)}
                          showDepartmentHeader={!isMultiColumn}
                          activeCardId={activeCardId}
                          onActivateCard={setActiveCardId}
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
