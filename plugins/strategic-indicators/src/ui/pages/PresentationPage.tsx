import { useEffect, useMemo, useState } from "react";
import { PresentationAlertsBoard } from "../components/PresentationAlertsBoard";
import { PresentationClosingPanel } from "../components/PresentationClosingPanel";
import { PresentationDepartmentBoard } from "../components/PresentationDepartmentBoard";
import { PresentationEdgeNavigation } from "../components/PresentationEdgeNavigation";
import { PresentationExecutiveStrip } from "../components/PresentationExecutiveStrip";
import { PresentationHero } from "../components/PresentationHero";
import { PresentationNarrativeStrip } from "../components/PresentationNarrativeStrip";
import { PresentationTopBar } from "../components/PresentationTopBar";
import { InfoState } from "../components/InfoState";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsPresentation } from "../../state/hooks/useStrategicIndicatorsPresentation";

type PresentationPageProps = {
  getAccessToken?: () => string | undefined;
};

type PresentationMode = "meeting" | "tv" | "slide";

type PresentationScene =
  | "overview"
  | "departments"
  | "department_detail"
  | "alerts"
  | "trend"
  | "closing";

function getCurrentMonthValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function buildMonthRange(monthValue: string) {
  if (!monthValue) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const [yearStr, monthStr] = monthValue.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (!year || !month) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const firstDay = `01-${String(month).padStart(2, "0")}-${year}`;
  const lastDayDate = new Date(year, month, 0);
  const lastDay = `${String(lastDayDate.getDate()).padStart(2, "0")}-${String(
    month,
  ).padStart(2, "0")}-${year}`;

  return {
    startDate: firstDay,
    endDate: lastDay,
  };
}

function getSceneOrder(): PresentationScene[] {
  return [
    "overview",
    "departments",
    "department_detail",
    "alerts",
    "trend",
    "closing",
  ];
}

function getSceneTitle(scene: PresentationScene) {
  switch (scene) {
    case "overview":
      return "Visão geral executiva";
    case "departments":
      return "Panorama dos departamentos";
    case "department_detail":
      return "Detalhe do departamento";
    case "alerts":
      return "Alertas executivos";
    case "trend":
      return "Tendência e evolução";
    case "closing":
      return "Fechamento executivo";
    default:
      return "Apresentação Executiva";
  }
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());
  const [mode, setMode] = useState<PresentationMode>("meeting");
  const [scene, setScene] = useState<PresentationScene>("overview");
  const [departmentIndex, setDepartmentIndex] = useState(0);

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const presentation = useStrategicIndicatorsPresentation({
    competence: referenceMonth,
    startDate,
    endDate,
    months: 3,
    getAccessToken,
  });

  const data = presentation.data;
  const orderedScenes = getSceneOrder();
  const currentSceneIndex = orderedScenes.indexOf(scene);

  const selectedDepartment = useMemo(() => {
    if (!data) {
      return null;
    }

    const focusedId = presentation.selectedDepartmentId;
    if (!focusedId) {
      return data.departments[departmentIndex] ?? data.departments[0] ?? null;
    }

    return (
      data.departments.find((department) => department.id === focusedId) ??
      data.departments[departmentIndex] ??
      data.departments[0] ??
      null
    );
  }, [data, departmentIndex, presentation.selectedDepartmentId]);

  useEffect(() => {
    if (!data || !presentation.selectedDepartmentId) {
      return;
    }

    const nextIndex = data.departments.findIndex(
      (department) => department.id === presentation.selectedDepartmentId,
    );

    if (nextIndex >= 0 && nextIndex !== departmentIndex) {
      setDepartmentIndex(nextIndex);
    }
  }, [data, departmentIndex, presentation.selectedDepartmentId]);

  function goToPrevious() {
    if (!data) return;

    if (scene === "department_detail") {
      if (departmentIndex > 0) {
        const nextIndex = departmentIndex - 1;
        const nextDepartmentId = presentation.departmentIds[nextIndex] ?? null;
        setDepartmentIndex(nextIndex);
        presentation.setFocusedDepartmentId(nextDepartmentId);
        return;
      }

      setScene("departments");
      return;
    }

    if (currentSceneIndex > 0) {
      setScene(orderedScenes[currentSceneIndex - 1]);
    }
  }

  function goToNext() {
    if (!data) return;

    if (scene === "department_detail") {
      if (departmentIndex < data.departments.length - 1) {
        const nextIndex = departmentIndex + 1;
        const nextDepartmentId = presentation.departmentIds[nextIndex] ?? null;
        setDepartmentIndex(nextIndex);
        presentation.setFocusedDepartmentId(nextDepartmentId);
        return;
      }

      setScene("alerts");
      return;
    }

    if (scene === "departments" && data.departments.length > 0) {
      setDepartmentIndex(0);
      presentation.setFocusedDepartmentId(presentation.departmentIds[0] ?? null);
      setScene("department_detail");
      return;
    }

    if (currentSceneIndex < orderedScenes.length - 1) {
      setScene(orderedScenes[currentSceneIndex + 1]);
    }
  }

  function renderDepartmentDetailScene() {
    if (!data || !selectedDepartment) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Nenhum departamento disponível"
            description="Não há dados suficientes para exibir o detalhamento do departamento."
          />
        </div>
      );
    }

    if (
      presentation.selectedDepartmentId &&
      data.departmentFocus &&
      data.departmentFocus.id !== presentation.selectedDepartmentId
    ) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Atualizando departamento"
            description="Aguarde enquanto os indicadores e a leitura executiva do departamento selecionado são atualizados."
          />
        </div>
      );
    }

    if (!data.departmentFocus) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Detalhamento indisponível"
            description="Não foi possível carregar o detalhamento do departamento selecionado."
          />
        </div>
      );
    }

    const focus = data.departmentFocus;
    const variation = selectedDepartment.current - selectedDepartment.previous;
    const topIndicators = focus.indicators
      .slice()
      .sort((a, b) => a.score - b.score)
      .slice(0, 4);

    return (
      <div className="si-presentation-department-slide">
        <section className="si-presentation-department-slide__hero">
          <div className="si-presentation-department-slide__hero-main">
            <span className="si-presentation-department-slide__eyebrow">
              Departamento em foco
            </span>
            <h2 className="si-presentation-department-slide__title">
              {selectedDepartment.name}
            </h2>
            <p className="si-presentation-department-slide__subtitle">
              Slide {departmentIndex + 1} de {data.departments.length}
            </p>
          </div>

          <div className="si-presentation-department-slide__hero-badge">
            <StatusBadge
              label={focus.variation.directionLabel}
              variant={
                focus.variation.direction === "up"
                  ? "success"
                  : focus.variation.direction === "down"
                    ? "warning"
                    : "neutral"
              }
            />
          </div>
        </section>

        <div className="si-presentation-department-slide__metrics">
          <article className="si-presentation-metric-card">
            <span>Score atual</span>
            <strong>{formatScore(focus.score)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Período anterior</span>
            <strong>{formatScore(selectedDepartment.previous)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Variação</span>
            <strong>
              {variation > 0 ? "+" : ""}
              {formatScore(variation)}
            </strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Contribuição no IGD</span>
            <strong>{formatScore(focus.contribution)}</strong>
          </article>
        </div>

        <div className="si-presentation-department-slide__bottom">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura executiva
            </span>
            <strong className="si-presentation-scene-card__value">
              {focus.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              {focus.strategicSummary ||
                "Departamento em evidência para aprofundamento executivo no período."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Agregação do departamento
            </span>
            <strong className="si-presentation-scene-card__value">
              {focus.aggregationMode}
            </strong>
            <p className="si-presentation-scene-card__text">
              Peso no IGD: {formatScore(focus.weightInIgd)}% · {focus.units.length} unidade(s) considerada(s).
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Indicadores que exigem atenção
            </span>
            <strong className="si-presentation-scene-card__value">
              {topIndicators.length}
            </strong>
            <p className="si-presentation-scene-card__text">
              {topIndicators.length > 0
                ? topIndicators
                    .map(
                      (indicator) =>
                        `${indicator.name} (${formatScore(indicator.score)})`,
                    )
                    .join(" • ")
                : "Nenhum indicador crítico identificado para o período."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Meta e direção de performance
            </span>
            <strong className="si-presentation-scene-card__value">
              {topIndicators[0]?.goalLabel ?? "Sem meta destacada"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {topIndicators[0]
                ? `${topIndicators[0].goalPeriodicity} · ${topIndicators[0].goalMode} · ${topIndicators[0].performanceDirection}`
                : "Não há indicador com meta destacada para exibir."}
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderTrendScene() {
    if (!data?.trend) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Tendência indisponível"
            description="Não foi possível consolidar a série histórica do período."
          />
        </div>
      );
    }

    const trend = data.trend;
    const highlightDepartment = trend.departments[0] ?? null;
    const latestSeries = trend.igdSeries.slice(-6);

    return (
      <div className="si-presentation-trend-scene">
        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">IGD atual</span>
            <strong className="si-presentation-scene-card__value">
              {formatScore(trend.currentIgd)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Classificação atual: {trend.currentClassification}.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">IGD anterior</span>
            <strong className="si-presentation-scene-card__value">
              {formatScore(trend.previousIgd)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Base comparativa para a leitura temporal do período.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Série recente do IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {latestSeries.length} pontos
            </strong>
            <p className="si-presentation-scene-card__text">
              {latestSeries
                .map((item) => `${item.period}: ${formatScore(item.value)}`)
                .join(" • ")}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Departamento em destaque
            </span>
            <strong className="si-presentation-scene-card__value">
              {highlightDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {highlightDepartment
                ? `Atual ${formatScore(highlightDepartment.current)} · Anterior ${formatScore(
                    highlightDepartment.previous,
                  )} · ${highlightDepartment.directionLabel}`
                : "Sem destaque departamental disponível para o período."}
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderAlertsScene() {
    if (!data) return null;

    const alertsToShow =
      data.alerts.executive.length > 0
        ? data.alerts.executive
        : data.executiveAlerts;

    return (
      <div className="si-presentation-single-scene">
        <PresentationAlertsBoard alerts={alertsToShow.slice(0, 3)} />
      </div>
    );
  }

  function renderScene() {
    if (presentation.loading) {
      return (
        <div className="si-presentation-loading-stage">
          <InfoState
            title="Carregando apresentação"
            description="Aguarde enquanto a visão executiva do IGD e dos departamentos é preparada."
          />
        </div>
      );
    }

    if (presentation.error || !data) {
      return (
        <div className="si-presentation-loading-stage">
          <InfoState
            title="Falha ao carregar apresentação"
            description={
              presentation.error ??
              "Não foi possível obter os dados necessários."
            }
            actionLabel="Tentar novamente"
            onAction={() => {
              void presentation.reload();
            }}
          />
        </div>
      );
    }

    if (scene === "overview") {
      return (
        <div className="si-presentation-overview-scene">
          <PresentationHero
            igd={data.igd}
            classification={data.classification}
            trendLabel={data.trendLabel}
          />

          <PresentationNarrativeStrip
            classification={data.classification}
            trendLabel={data.trendLabel}
            topDepartment={data.topDepartment}
            topRisk={data.topRisk}
          />

          <PresentationExecutiveStrip
            currentIgd={data.currentIgd}
            previousIgd={data.previousIgd}
            variationValue={data.variationValue}
            topDepartment={data.topDepartment}
            topRisk={data.topRisk}
          />
        </div>
      );
    }

    if (scene === "departments") {
      return (
        <div className="si-presentation-single-scene">
          <PresentationDepartmentBoard
            departments={data.departments.slice(0, 6)}
          />
        </div>
      );
    }

    if (scene === "department_detail") {
      return renderDepartmentDetailScene();
    }

    if (scene === "alerts") {
      return renderAlertsScene();
    }

    if (scene === "trend") {
      return renderTrendScene();
    }

    return (
      <div className="si-presentation-single-scene">
        <PresentationClosingPanel
          currentPeriod={data.currentPeriod}
          previousPeriod={data.previousPeriod}
          classification={data.classification}
          trendLabel={data.trendLabel}
          topDepartment={data.topDepartment}
          topRisk={data.topRisk}
        />
      </div>
    );
  }

  const previousDisabled = presentation.loading || !data || scene === "overview";
  const nextDisabled = presentation.loading || !data || scene === "closing";
  const warningMessage = presentation.warnings[0]?.message ?? null;

  return (
    <div className={`si-presentation-page si-presentation-page--${mode}`}>
      <div className="si-presentation-viewport">
        <PresentationTopBar
          competence={data?.competence ?? referenceMonth}
          sceneTitle={getSceneTitle(scene)}
          mode={mode}
          isRefreshing={presentation.refreshing || presentation.loading}
          referenceMonth={referenceMonth}
          onReferenceMonthChange={setReferenceMonth}
          onModeChange={setMode}
        />

        <div className="si-presentation-stage">
          {warningMessage && data ? (
            <div className="si-presentation-stage__feedback">
              <InfoState
                title="Atualização parcial da apresentação"
                description={warningMessage}
                actionLabel="Tentar novamente"
                onAction={() => {
                  void presentation.reload();
                }}
              />
            </div>
          ) : null}

          <div className="si-presentation-scene-frame">{renderScene()}</div>
        </div>

        <PresentationEdgeNavigation
          onPrevious={goToPrevious}
          onNext={goToNext}
          previousDisabled={previousDisabled}
          nextDisabled={nextDisabled}
        />
      </div>
    </div>
  );
}