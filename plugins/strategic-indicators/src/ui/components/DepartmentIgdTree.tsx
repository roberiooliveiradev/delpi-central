import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { ChevronDown, ExternalLink } from "lucide-react";
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
import {
  getScoreStatusVariant,
  type ScoreStatusVariant,
} from "../shared/scoreVariant";
import { getScopeTypeLabel } from "../presentation/labels";
import { StatusBadge } from "./StatusBadge";
import { PanZoomCanvas } from "./PanZoomCanvas";
import { TreeScoreRing } from "./TreeScoreRing";
import { TreeSparkline } from "./TreeSparkline";
import "./DepartmentSummaryCard.css";
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
      <span className="si-tree-card__open">
        <ExternalLink size={14} aria-hidden />
        Abrir
      </span>
      <strong className="si-org-chart__node-title">{title}</strong>
      {subtitle ? (
        <span className="si-org-chart__node-subtitle">{subtitle}</span>
      ) : null}
      {meta ? <span className="si-org-chart__node-meta">{meta}</span> : null}
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
  const tone = indicator.hasValue
    ? getScoreStatusVariant(indicator.score ?? 0)
    : "empty";

  return (
    <InteractiveTreeCard
      href={href}
      cardId={cardId}
      isActive={isActive}
      onActivate={onActivate}
      className={`si-department-card si-tree-indicator-card si-tree-indicator-card--${tone}`}
    >
      <div className="si-department-card__top si-tree-indicator-card__top">
        <div className="si-department-card__identity">
          <div>
            <h3 className="si-department-card__title">{indicator.name}</h3>
            <p className="si-department-card__weight">
              Peso {indicator.weightPct}%
            </p>
          </div>
        </div>
        {!isMissingValueClassification(indicator.classification) ? (
          <StatusBadge
            label={
              indicator.hasValue
                ? (indicator.score ?? 0).toFixed(1)
                : indicator.classification
            }
            variant={tone === "empty" ? "neutral" : tone}
          />
        ) : (
          <StatusBadge label="Sem dado" variant="neutral" />
        )}
      </div>

      <div className="si-tree-indicator-card__charts">
        <TreeSparkline
          points={series}
          direction={indicator.trend}
          height={48}
          label="Histórico · 6 meses"
        />
      </div>

      <div className="si-department-card__metrics si-tree-indicator-card__metrics">
        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">Meta</span>
          <strong>{formatIndicatorGoalValue(indicator, competence)}</strong>
        </div>
        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">Realizado</span>
          <strong>
            {formatIndicatorRealizedDisplay(indicator, valueFormat)}
          </strong>
        </div>
        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">Nota</span>
          <strong
            className={`si-department-card__metric-value${
              !indicator.hasValue ? " si-tree-indicator__value--missing" : ""
            }`}
          >
            {formatIndicatorScore(indicator.score)}
          </strong>
        </div>
        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">Gap</span>
          <strong
            className={`si-department-card__metric-value${
              !indicator.hasValue ? " si-tree-indicator__value--missing" : ""
            }`}
          >
            {formatIndicatorGapDisplay(indicator, valueFormat)}
          </strong>
        </div>
      </div>

      <p className="si-tree-indicator-card__meta">
        {getTrendLabel(indicator.trend)} · {getScopeTypeLabel(indicator.scopeType)}
      </p>
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
    <PanZoomCanvas
      fitToken={fitToken}
      toolbar={toolbar}
      className="si-org-chart-canvas"
    >
      <div className="si-org-chart" style={chartStyle}>
        <section className="si-org-chart__level si-org-chart__level--igd">
          <span className="si-org-chart__level-tag">Nível 1</span>
          <InteractiveTreeCard
            href={appendStrategicIndicatorsFiltersToPath(
              "/apps/strategic-indicators",
              filterState,
            )}
            cardId="igd:root"
            isActive={activeCardId === "igd:root"}
            onActivate={setActiveCardId}
            className="si-org-chart__igd-card"
          >
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
            {model.igd !== null ? (
              <div className="si-org-chart__igd-charts">
                <TreeScoreRing
                  score={model.igd}
                  label="IGD"
                  tone="igd"
                  size={80}
                />
                <TreeSparkline
                  points={model.igdSeries}
                  direction="stable"
                  height={54}
                  label="Evolução IGD"
                />
              </div>
            ) : null}
          </InteractiveTreeCard>
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
                <InteractiveTreeCard
                  href={buildTrendsHref(filterState, column.scope)}
                  cardId={`scope:${column.scope.key}`}
                  isActive={activeCardId === `scope:${column.scope.key}`}
                  onActivate={setActiveCardId}
                  className="si-org-chart__scope-card"
                >
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
                  {column.averageScore !== null ? (
                    <TreeScoreRing
                      score={column.averageScore}
                      label="Média"
                      tone="scope"
                      size={68}
                    />
                  ) : null}
                </InteractiveTreeCard>
              </div>
            ))}
          </div>
        </section>

        <OrgChartArrow />

        <section className="si-org-chart__level si-org-chart__level--departments">
          <span className="si-org-chart__level-tag">
            Nível 3 · Departamentos · Nível 4 · Indicadores
          </span>

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
