import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
} from "react";
import { ChevronDown } from "lucide-react";
import type { IndicatorViewItem } from "../../data/types/indicators";
import {
  pickActiveTreeColumn,
  resolveActiveTreeScopeKey,
} from "../../data/departmentTreeScopes";
import type {
  DepartmentTreeDepartmentNode,
  DepartmentTreeIndicatorNode,
  DepartmentTreeModel,
  DepartmentTreeScopeConfig,
  DepartmentTreeScopeKey,
} from "../../data/types/departmentTree";
import type { StrategicIndicatorsFilterState } from "../shared/strategicIndicatorsFilterUrl";
import { appendStrategicIndicatorsFiltersToPath } from "../shared/strategicIndicatorsFilterUrl";
import { navigateStrategicIndicators } from "../shared/strategicIndicatorsNavigation";
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
import { IGD_HERO_DESCRIPTION } from "./IgdHeroCard";
import "./IgdHeroCard.css";
import "./DepartmentIgdTree.css";

type DepartmentIgdTreeFilterControls = {
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
  status?: ReactNode;
};

type DepartmentIgdTreeProps = {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  filterControls: DepartmentIgdTreeFilterControls;
};

type IndicatorListLayout = "row" | "multi-grid" | "multi-stack";

function resolveIndicatorListLayout(
  expandedDepartmentCount: number,
): IndicatorListLayout {
  if (expandedDepartmentCount === 1) {
    return "row";
  }

  if (expandedDepartmentCount === 2) {
    return "multi-grid";
  }

  return "multi-stack";
}

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

function TreeIgdCard({
  model,
  filterState,
  cardId,
  isActive,
  onActivate,
  departmentsVisible,
  departmentCount,
  onToggleDepartments,
}: {
  model: DepartmentTreeModel;
  filterState: StrategicIndicatorsFilterState;
  cardId: string;
  isActive: boolean;
  onActivate: (cardId: string) => void;
  departmentsVisible: boolean;
  departmentCount: number;
  onToggleDepartments: () => void;
}) {
  const igdBadgeVariant =
    model.igd !== null
      ? mapScoreToBadgeVariant(model.igd)
      : ("neutral" as const);

  return (
    <div className="si-org-chart__igd-stack">
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
          <div className="si-igd-hero__content">
            <p className="si-igd-hero__eyebrow">Índice Global Delpi</p>

            <div className="si-igd-hero__headline">
              <div>
                <h2 className="si-igd-hero__value">
                  IGD: {model.igd !== null ? model.igd.toFixed(1) : "—"}
                </h2>
                <p className="si-igd-hero__exact">
                  {model.igdExact !== null
                    ? `cálculo consolidado: ${model.igdExact.toFixed(3)}`
                    : `Competência ${model.competence}`}
                </p>
              </div>
              {model.classification ? (
                <StatusBadge
                  label={model.classification}
                  variant={igdBadgeVariant}
                />
              ) : null}
            </div>

            <p className="si-igd-hero__description">{IGD_HERO_DESCRIPTION}</p>
          </div>

          {model.igdSeries.length > 0 ? (
            <TreeSparkline
              points={model.igdSeries}
              direction="stable"
              height={56}
              label="Evolução · últimos meses"
            />
          ) : null}
        </section>
      </InteractiveTreeCard>

      {departmentCount > 0 ? (
        <button
          type="button"
          className="si-org-chart__igd-toggle"
          data-pan-zoom-lock="true"
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onToggleDepartments();
          }}
          aria-expanded={departmentsVisible}
        >
          <span>
            {departmentsVisible
              ? "Recolher departamentos"
              : `Expandir ${departmentCount} departamentos`}
          </span>
          <ChevronDown
            size={18}
            className={
              departmentsVisible ? "si-org-chart__igd-chevron--open" : undefined
            }
            aria-hidden
          />
        </button>
      ) : null}
    </div>
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
  const handleNavigate = (event: MouseEvent<HTMLAnchorElement>) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    event.preventDefault();
    navigateStrategicIndicators(href);
  };

  return (
    <a
      href={href}
      className={`${className} si-tree-card--interactive${
        isActive ? " si-tree-card--active" : ""
      }`}
      onMouseDown={() => onActivate(cardId)}
      onFocus={() => onActivate(cardId)}
      onClick={handleNavigate}
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
  indicatorListLayout,
  isSoloExpandedDepartment,
  onToggle,
  activeCardId,
  onActivateCard,
}: {
  node: DepartmentTreeDepartmentNode | null;
  scope: DepartmentTreeScopeConfig;
  filterState: StrategicIndicatorsFilterState;
  competence: string;
  expanded: boolean;
  indicatorListLayout: IndicatorListLayout;
  isSoloExpandedDepartment: boolean;
  onToggle: () => void;
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
              <span className="si-department-card__short">
                {department.shortName}
              </span>
              <div>
                <h3 className="si-department-card__title">{department.name}</h3>
                <p className="si-department-card__weight">
                  peso no IGD: {department.weightInIgd}%
                </p>
              </div>
            </div>

            <StatusBadge
              label={department.score.toFixed(1)}
              variant={cardVariant}
            />
          </div>

          <p className="si-department-card__summary">
            {department.strategicSummary}
          </p>

          <div className="si-department-card__goal">
            <span className="si-department-card__goal-label">
              Referência executiva
            </span>
            <strong className="si-department-card__goal-value">
              {department.classification}
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
        <section
          className={`si-tree-dept__indicators${
            isSoloExpandedDepartment
              ? " si-tree-dept__indicators--solo-expanded"
              : ""
          }`}
          data-pan-zoom-lock="true"
        >
          <OrgChartArrow />
          <div
            className={`si-tree-dept__indicator-list si-tree-dept__indicator-list--${indicatorListLayout}`}
          >
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

export function DepartmentIgdTree({
  model,
  filterState,
  filterControls,
}: DepartmentIgdTreeProps) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => new Set());
  const [departmentsVisible, setDepartmentsVisible] = useState(true);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  const activeScopeKey = resolveActiveTreeScopeKey(
    filterControls.viewMode,
    filterControls.branch,
  );

  const activeColumn = useMemo(
    () => pickActiveTreeColumn(model.columns, activeScopeKey),
    [model.columns, activeScopeKey],
  );

  const nodesById = useMemo(
    () =>
      new Map(
        (activeColumn?.departments ?? []).map((item) => [
          item.department.id,
          item,
        ]),
      ),
    [activeColumn],
  );

  const allExpandableKeys = useMemo(() => {
    if (!activeColumn) {
      return [];
    }

    const keys: string[] = [];

    for (const departmentId of model.departmentOrder) {
      const node = nodesById.get(departmentId);
      if (node && node.indicators.length > 0) {
        keys.push(`${activeColumn.scope.key}:${departmentId}`);
      }
    }

    return keys;
  }, [activeColumn, model.departmentOrder, nodesById]);

  const treeLayoutKey = `${model.competence}-${activeScopeKey}-${model.departmentOrder.join("|")}`;

  useEffect(() => {
    setExpandedKeys(new Set());
    setDepartmentsVisible(true);
  }, [treeLayoutKey]);

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
    setDepartmentsVisible(true);
    setExpandedKeys(new Set(allExpandableKeys));
  }, [allExpandableKeys]);

  const collapseAll = useCallback(() => {
    setDepartmentsVisible(false);
    setExpandedKeys(new Set());
  }, []);

  const toggleDepartmentsVisible = useCallback(() => {
    setDepartmentsVisible((current) => !current);
  }, []);

  const hasExpandable = allExpandableKeys.length > 0;

  const expandedDepartmentIds = useMemo(() => {
    if (!activeColumn) {
      return [];
    }

    return model.departmentOrder.filter((departmentId) => {
      const expandKey = `${activeColumn.scope.key}:${departmentId}`;
      if (!expandedKeys.has(expandKey)) {
        return false;
      }

      const node = nodesById.get(departmentId);
      return Boolean(node && node.indicators.length > 0);
    });
  }, [activeColumn, expandedKeys, model.departmentOrder, nodesById]);

  const expandedDepartmentCount = expandedDepartmentIds.length;
  const soloExpandedDepartmentId =
    expandedDepartmentCount === 1 ? expandedDepartmentIds[0] : null;

  const departmentCount = model.departmentOrder.length;

  const fitToken = treeLayoutKey;

  const chartStyle = {
    "--si-org-chart-cols": "1",
    "--si-dept-count": String(departmentCount),
    "--si-dept-slot-width": "420px",
    "--si-dept-gap": "28px",
  } as CSSProperties;

  const isTreeFullyExpanded =
    departmentsVisible &&
    (allExpandableKeys.length === 0 ||
      allExpandableKeys.every((key) => expandedKeys.has(key)));

  const isTreeFullyCollapsed = !departmentsVisible && expandedKeys.size === 0;

  const mapActions =
    departmentCount > 0 || hasExpandable ? (
      <div
        className="si-tree-view-toggle"
        role="group"
        aria-label="Expandir ou recolher organograma"
      >
        <button
          type="button"
          className={`si-tree-view-toggle__btn${
            isTreeFullyExpanded ? " si-tree-view-toggle__btn--active" : ""
          }`}
          onClick={expandAll}
          aria-pressed={isTreeFullyExpanded}
        >
          Expandir tudo
        </button>
        <button
          type="button"
          className={`si-tree-view-toggle__btn${
            isTreeFullyCollapsed ? " si-tree-view-toggle__btn--active" : ""
          }`}
          onClick={collapseAll}
          aria-pressed={isTreeFullyCollapsed}
        >
          Recolher tudo
        </button>
      </div>
    ) : null;

  const renderFloatingControls = (viewportNav: ReactNode) => (
    <TreeMapFloatingControls
      referenceMonth={filterControls.referenceMonth}
      viewMode={filterControls.viewMode}
      branch={filterControls.branch}
      treeScope={filterControls.treeScope}
      monthsToCompare={filterControls.monthsToCompare}
      onReferenceMonthChange={filterControls.onReferenceMonthChange}
      onViewModeChange={filterControls.onViewModeChange}
      onBranchChange={filterControls.onBranchChange}
      onTreeScopeChange={filterControls.onTreeScopeChange}
      onMonthsToCompareChange={filterControls.onMonthsToCompareChange}
      viewportNav={viewportNav}
      actions={mapActions}
      status={filterControls.status}
    />
  );

  return (
    <PanZoomCanvas
      fitToken={fitToken}
      immersive
      floatingControls={renderFloatingControls}
      className="si-org-chart-canvas"
    >
      <div
        className="si-org-chart si-org-chart--single-scope"
        style={chartStyle}
      >
        <section className="si-org-chart__level si-org-chart__level--igd">
          <span className="si-org-chart__level-tag">IGD</span>
          <TreeIgdCard
            model={model}
            filterState={filterState}
            cardId="igd:root"
            isActive={activeCardId === "igd:root"}
            onActivate={setActiveCardId}
            departmentsVisible={departmentsVisible}
            departmentCount={departmentCount}
            onToggleDepartments={toggleDepartmentsVisible}
          />
        </section>

        {departmentsVisible && departmentCount > 0 ? (
          <>
            <OrgChartArrow />

            <section className="si-org-chart__level si-org-chart__level--departments">
              <span className="si-org-chart__level-tag">
                Departamentos e indicadores
              </span>

              <div className="si-org-chart__departments-fork">
                <div className="si-org-chart__departments-connector">
                  <div
                    className={`si-org-chart__departments-row${
                    expandedDepartmentCount === 1
                      ? " si-org-chart__departments-row--one-expanded"
                      : ""
                  }${
                    expandedDepartmentCount >= 2
                      ? " si-org-chart__departments-row--multi-expanded"
                      : ""
                  }`}
                >
            {model.departmentOrder.map((departmentId) => {
              const expandKey = activeColumn
                ? `${activeColumn.scope.key}:${departmentId}`
                : "";
              const isDepartmentExpanded = expandedKeys.has(expandKey);

              return (
              <div
                key={departmentId}
                className={`si-org-chart__department-column${
                  soloExpandedDepartmentId === departmentId
                    ? " si-org-chart__department-column--solo-expanded"
                    : ""
                }${
                  isDepartmentExpanded
                    ? " si-org-chart__department-column--open"
                    : ""
                }`}
              >
                <div className="si-org-chart__department-scopes">
                  {activeColumn ? (
                    <div className="si-org-chart__department-scope">
                      <DepartmentTreeCard
                        node={nodesById.get(departmentId) ?? null}
                        scope={activeColumn.scope}
                        filterState={filterState}
                        competence={model.competence}
                        expanded={isDepartmentExpanded}
                        indicatorListLayout={
                          soloExpandedDepartmentId === departmentId
                            ? "row"
                            : resolveIndicatorListLayout(expandedDepartmentCount)
                        }
                        isSoloExpandedDepartment={
                          soloExpandedDepartmentId === departmentId
                        }
                        onToggle={() => toggleDepartment(expandKey)}
                        activeCardId={activeCardId}
                        onActivateCard={setActiveCardId}
                      />
                    </div>
                  ) : null}
                </div>
              </div>
            );
            })}
                  </div>
                </div>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </PanZoomCanvas>
  );
}
