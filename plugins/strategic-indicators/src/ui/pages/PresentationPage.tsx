import { useEffect, useMemo, useRef, useState } from "react";
import { PresentationAlertsBoard } from "../components/PresentationAlertsBoard";
import { PresentationClosingPanel } from "../components/PresentationClosingPanel";
import { PresentationDepartmentBoard } from "../components/PresentationDepartmentBoard";
import { PresentationEdgeNavigation } from "../components/PresentationEdgeNavigation";
import { PresentationExecutiveStrip } from "../components/PresentationExecutiveStrip";
import { PresentationHero } from "../components/PresentationHero";
import { PresentationNarrativeStrip } from "../components/PresentationNarrativeStrip";
import { PresentationTopBar } from "../components/PresentationTopBar";
import { InfoState } from "../components/InfoState";
import type {
  PresentationDepartmentBoardItem,
  PresentationDepartmentFocus,
} from "../../data/types/presentation";
import { useStrategicIndicatorsPresentation } from "../../state/hooks/useStrategicIndicatorsPresentation";
import {
  buildStrategicIndicatorsMonthRange,
  getCurrentStrategicIndicatorsMonthValue,
  resolveStrategicIndicatorsBranch,
  STRATEGIC_INDICATORS_BRANCH_OPTIONS,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";

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

const PRESENTATION_MODE_STORAGE_KEY = "si:presentation:mode";
const PRESENTATION_VIEW_MODE_STORAGE_KEY = "si:presentation:view-mode";
const PRESENTATION_BRANCH_STORAGE_KEY = "si:presentation:branch";
const PRESENTATION_MONTHS_STORAGE_KEY = "si:presentation:months";

const PRESENTATION_MONTHS_OPTIONS = [
  { value: 3, label: "3 meses" },
  { value: 6, label: "6 meses" },
  { value: 12, label: "12 meses" },
] as const;

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

function getSceneAutoplayMs(
  scene: PresentationScene,
  mode: PresentationMode,
): number {
  const baseByScene: Record<PresentationScene, number> = {
    overview: 8000,
    departments: 10000,
    department_detail: 14000,
    alerts: 10000,
    trend: 10000,
    closing: 12000,
  };

  const base = baseByScene[scene];

  if (mode === "tv") {
    return base;
  }

  if (mode === "slide") {
    return base + 2000;
  }

  return base;
}

function getAdaptiveSceneAutoplayMs(params: {
  scene: PresentationScene;
  mode: PresentationMode;
  criticalIndicatorsCount?: number;
  executiveAlertsCount?: number;
  departmentAlertsCount?: number;
  indicatorAlertsCount?: number;
  trendPointsCount?: number;
}) {
  const {
    scene,
    mode,
    criticalIndicatorsCount = 0,
    executiveAlertsCount = 0,
    departmentAlertsCount = 0,
    indicatorAlertsCount = 0,
    trendPointsCount = 0,
  } = params;

  const base = getSceneAutoplayMs(scene, mode);

  if (scene === "department_detail") {
    const criticalBonus = Math.min(criticalIndicatorsCount, 6) * 1000;
    return base + criticalBonus;
  }

  if (scene === "alerts") {
    const totalAlerts =
      executiveAlertsCount + departmentAlertsCount + indicatorAlertsCount;
    const alertsBonus = Math.min(totalAlerts, 8) * 500;
    return base + alertsBonus;
  }

  if (scene === "trend") {
    const trendBonus = Math.min(trendPointsCount, 6) * 400;
    return base + trendBonus;
  }

  return base;
}

function getDirectionLabel(direction: "up" | "down" | "stable") {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getDirectionVariant(direction: "up" | "down" | "stable") {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatPct(value: number) {
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function readStoredPresentationMode(): PresentationMode {
  if (typeof window === "undefined") return "meeting";
  const value = window.localStorage.getItem(PRESENTATION_MODE_STORAGE_KEY);
  return value === "tv" || value === "slide" || value === "meeting"
    ? value
    : "meeting";
}

function readStoredPresentationViewMode(): StrategicIndicatorsViewMode {
  if (typeof window === "undefined") return "consolidated";
  const value = window.localStorage.getItem(PRESENTATION_VIEW_MODE_STORAGE_KEY);
  return value === "branch" || value === "consolidated"
    ? value
    : "consolidated";
}

function readStoredPresentationBranch(): string {
  if (typeof window === "undefined") return "01";
  return window.localStorage.getItem(PRESENTATION_BRANCH_STORAGE_KEY) || "01";
}

function readStoredPresentationMonths(): number {
  if (typeof window === "undefined") return 3;

  const rawValue = window.localStorage.getItem(PRESENTATION_MONTHS_STORAGE_KEY);
  const parsedValue = Number(rawValue);

  if ([3, 6, 12].includes(parsedValue)) {
    return parsedValue;
  }

  return 3;
}

function buildSelectedDepartment(
  boardDepartment: PresentationDepartmentBoardItem | null,
  focus: PresentationDepartmentFocus | null,
) {
  if (!boardDepartment && !focus) return null;

  const sameDepartment =
    Boolean(boardDepartment) &&
    Boolean(focus) &&
    boardDepartment!.id === focus!.id;

  const safeFocus = sameDepartment ? focus : null;

  return {
    id: boardDepartment?.id ?? safeFocus?.id ?? "",
    name: boardDepartment?.name ?? safeFocus?.name ?? "—",
    score: safeFocus?.score ?? boardDepartment?.current ?? 0,
    previous:
      boardDepartment?.previous ??
      Math.max(0, (safeFocus?.score ?? 0) - (safeFocus?.variation.value ?? 0)),
    direction:
      safeFocus?.variation.direction ?? boardDepartment?.direction ?? "stable",
    classification: safeFocus?.classification ?? "—",
    contribution: safeFocus?.contribution ?? 0,
    weightInIgd: safeFocus?.weightInIgd ?? 0,
    aggregationMode: safeFocus?.aggregationMode ?? "—",
    strategicSummary:
      safeFocus?.strategicSummary ??
      "Departamento em evidência para aprofundamento executivo.",
    units: safeFocus?.units ?? [],
    indicators: safeFocus?.indicators ?? [],
    variationValue:
      safeFocus?.variation.value ??
      ((boardDepartment?.current ?? 0) - (boardDepartment?.previous ?? 0)),
    variationLabel:
      safeFocus?.variation.directionLabel ??
      getDirectionLabel(boardDepartment?.direction ?? "stable"),
  };
}

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(
    getCurrentStrategicIndicatorsMonthValue(),
  );
  const [mode, setMode] = useState<PresentationMode>(() =>
    readStoredPresentationMode(),
  );
  const [viewMode, setViewMode] = useState<StrategicIndicatorsViewMode>(() =>
    readStoredPresentationViewMode(),
  );
  const [branch, setBranch] = useState(() => readStoredPresentationBranch());
  const [months, setMonths] = useState(() => readStoredPresentationMonths());
  const [scene, setScene] = useState<PresentationScene>("overview");
  const [departmentIndex, setDepartmentIndex] = useState(0);
  const [isAutoplayPaused, setIsAutoplayPaused] = useState(false);

  const autoplayResumeTimerRef = useRef<number | null>(null);

  const { startDate, endDate } = useMemo(
    () => buildStrategicIndicatorsMonthRange(referenceMonth),
    [referenceMonth],
  );

  const effectiveBranch = useMemo(
    () => resolveStrategicIndicatorsBranch(viewMode, branch),
    [viewMode, branch],
  );

  const presentation = useStrategicIndicatorsPresentation({
    competence: referenceMonth,
    branch: effectiveBranch,
    startDate,
    endDate,
    months,
    getAccessToken,
  });

  const data = presentation.data;
  const loading = presentation.loading;

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(PRESENTATION_MODE_STORAGE_KEY, mode);
  }, [mode]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(PRESENTATION_VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(PRESENTATION_BRANCH_STORAGE_KEY, branch);
  }, [branch]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      PRESENTATION_MONTHS_STORAGE_KEY,
      String(months),
    );
  }, [months]);

  function clearAutoplayResumeTimer() {
    if (typeof window === "undefined") return;

    if (autoplayResumeTimerRef.current !== null) {
      window.clearTimeout(autoplayResumeTimerRef.current);
      autoplayResumeTimerRef.current = null;
    }
  }

  function resetDeck() {
    setScene("overview");
    setDepartmentIndex(0);
    presentation.setFocusedDepartmentId(null);
  }

  function pauseAutoplayTemporarily(timeoutMs = 15000) {
    if (typeof window === "undefined") return;

    setIsAutoplayPaused(true);
    clearAutoplayResumeTimer();

    autoplayResumeTimerRef.current = window.setTimeout(() => {
      setIsAutoplayPaused(false);
      autoplayResumeTimerRef.current = null;
    }, timeoutMs);
  }

  function pauseAndResetDeck(timeoutMs = 15000) {
    pauseAutoplayTemporarily(timeoutMs);
    resetDeck();
  }

  useEffect(() => {
    return () => {
      clearAutoplayResumeTimer();
    };
  }, []);

  useEffect(() => {
    pauseAndResetDeck();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewMode, branch, referenceMonth, months]);

  useEffect(() => {
    if (!presentation.departmentIds.length) {
      return;
    }

    const nextDepartmentId =
      presentation.departmentIds[departmentIndex] ??
      presentation.departmentIds[0] ??
      null;

    presentation.setFocusedDepartmentId(nextDepartmentId);
  }, [
    departmentIndex,
    presentation.departmentIds,
    presentation.setFocusedDepartmentId,
  ]);

  useEffect(() => {
    if (!data?.departments.length) {
      return;
    }

    if (departmentIndex > data.departments.length - 1) {
      setDepartmentIndex(0);
    }
  }, [departmentIndex, data?.departments.length]);

  const orderedScenes = getSceneOrder();
  const currentSceneIndex = orderedScenes.indexOf(scene);

  function goToPrevious() {
    if (!data) return;

    if (scene === "department_detail") {
      if (departmentIndex > 0) {
        setDepartmentIndex((current) => current - 1);
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
        setDepartmentIndex((current) => current + 1);
        return;
      }
      setScene("alerts");
      return;
    }

    if (scene === "departments" && data.departments.length > 0) {
      setDepartmentIndex(0);
      setScene("department_detail");
      return;
    }

    if (currentSceneIndex < orderedScenes.length - 1) {
      setScene(orderedScenes[currentSceneIndex + 1]);
      return;
    }

    if (mode !== "meeting") {
      resetDeck();
    }
  }

  function handlePrevious() {
    pauseAutoplayTemporarily();
    goToPrevious();
  }

  function handleNext() {
    pauseAutoplayTemporarily();
    goToNext();
  }

  function handleModeChange(nextMode: PresentationMode) {
    pauseAndResetDeck();
    setMode(nextMode);
  }

  function handleViewModeChange(nextViewMode: StrategicIndicatorsViewMode) {
    pauseAndResetDeck();
    setViewMode(nextViewMode);
  }

  function handleBranchChange(nextBranch: string) {
    pauseAndResetDeck();
    setBranch(nextBranch);
  }

  function handleReferenceMonthChange(nextReferenceMonth: string) {
    pauseAndResetDeck();
    setReferenceMonth(nextReferenceMonth);
  }

  function handleMonthsChange(nextMonths: number) {
    pauseAndResetDeck();
    setMonths(nextMonths);
  }

  const selectedBoardDepartment =
    data?.departments[departmentIndex] ?? data?.departments[0] ?? null;

  const selectedFocus =
    data?.departmentFocus &&
    selectedBoardDepartment &&
    data.departmentFocus.id === selectedBoardDepartment.id
      ? data.departmentFocus
      : null;

  const selectedDepartment = buildSelectedDepartment(
    selectedBoardDepartment,
    selectedFocus,
  );

  const mostCriticalDepartmentOverview = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)[0];

  const trendHighlightUp = [...(data?.trend?.departments ?? [])].sort(
    (a, b) => b.current - b.previous - (a.current - a.previous),
  )[0];

  const trendHighlightDown = [...(data?.trend?.departments ?? [])].sort(
    (a, b) => a.current - a.previous - (b.current - b.previous),
  )[0];

  const executiveAlertsCount = data?.alerts.executive.length ?? 0;
  const departmentAlertsCount = data?.alerts.departments.length ?? 0;
  const indicatorAlertsCount = data?.alerts.indicators.length ?? 0;

  const mostPositiveDepartmentOverview = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.score - a.score)[0];

  const departmentsByLowestScore = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)
    .slice(0, 3);

  const departmentsByHighestWeight = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.weightInIgd - a.weightInIgd)
    .slice(0, 3);

  const strongestDepartmentCard = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.score - a.score)[0];

  const weakestDepartmentCard = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)[0];

  const highestWeightDepartment = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.weightInIgd - a.weightInIgd)[0];

  const selectedDepartmentIndicatorsSorted = selectedDepartment
    ? [...selectedDepartment.indicators].sort((a, b) => a.score - b.score)
    : [];

  const selectedDepartmentWorstIndicator =
    selectedDepartmentIndicatorsSorted[0] ?? null;

  const selectedDepartmentBestIndicator =
    [...selectedDepartmentIndicatorsSorted].sort((a, b) => b.score - a.score)[0] ??
    null;

  const selectedDepartmentCriticalIndicatorsCount =
    selectedDepartment?.indicators.filter((item) => item.score < 7).length ?? 0;

  const selectedDepartmentExcellentIndicatorsCount =
    selectedDepartment?.indicators.filter((item) => item.score >= 9).length ?? 0;

  const trendPointsCount = data?.trend?.igdSeries.length ?? 0;

  const currentSceneAutoplayMs = getAdaptiveSceneAutoplayMs({
    scene,
    mode,
    criticalIndicatorsCount: selectedDepartmentCriticalIndicatorsCount,
    executiveAlertsCount,
    departmentAlertsCount,
    indicatorAlertsCount,
    trendPointsCount,
  });

  useEffect(() => {
    if (mode === "meeting") return;
    if (loading || !data) return;
    if (isAutoplayPaused) return;

    const timer = window.setTimeout(() => {
      goToNext();
    }, currentSceneAutoplayMs);

    return () => window.clearTimeout(timer);
  }, [
    mode,
    loading,
    data,
    scene,
    departmentIndex,
    isAutoplayPaused,
    currentSceneAutoplayMs,
  ]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        pauseAutoplayTemporarily();
        goToPrevious();
      }

      if (event.key === "ArrowRight" || event.key === " ") {
        event.preventDefault();
        pauseAutoplayTemporarily();
        goToNext();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  function renderOverviewScene() {
    if (!data) return null;

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

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Fechamento atual
            </span>
            <strong className="si-presentation-scene-card__value">
              {formatScore(data.currentIgd)}
            </strong>
            <p className="si-presentation-scene-card__text">
              IGD consolidado da competência {data.currentPeriod}.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Fechamento anterior
            </span>
            <strong className="si-presentation-scene-card__value">
              {formatScore(data.previousIgd)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Base comparativa usada para leitura de tendência.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor departamento
            </span>
            <strong className="si-presentation-scene-card__value">
              {strongestDepartmentCard?.name ?? data.topDepartment}
            </strong>
            <p className="si-presentation-scene-card__text">
              Score atual de{" "}
              {strongestDepartmentCard
                ? formatScore(strongestDepartmentCard.score)
                : "—"}
              .
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior ponto de atenção
            </span>
            <strong className="si-presentation-scene-card__value">
              {weakestDepartmentCard?.name ?? data.topRisk}
            </strong>
            <p className="si-presentation-scene-card__text">
              Menor score consolidado no período atual.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior peso no IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {highestWeightDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Peso de{" "}
              {highestWeightDepartment
                ? formatPct(highestWeightDepartment.weightInIgd)
                : "—"}{" "}
              na composição do índice global.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura executiva
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              {data.trendLabel} com foco principal em {data.topRisk}.
            </p>
          </article>
        </div>

        <div className="si-presentation-trend-scene__grid">
          {data.kpis.map((kpi) => (
            <article key={kpi.id} className="si-presentation-scene-card">
              <span className="si-presentation-scene-card__label">
                {kpi.label}
              </span>
              <strong className="si-presentation-scene-card__value">
                {kpi.value}
              </strong>
              <p className="si-presentation-scene-card__text">
                {kpi.support ?? "Leitura executiva do período."}
              </p>
            </article>
          ))}
        </div>
      </div>
    );
  }

  function renderDepartmentsScene() {
    if (!data) return null;

    return (
      <div className="si-presentation-single-scene">
        <PresentationDepartmentBoard departments={data.departments.slice(0, 6)} />

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor departamento
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.topDepartment}
            </strong>
            <p className="si-presentation-scene-card__text">
              Área com melhor leitura consolidada no período atual.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Principal ponto de atenção
            </span>
            <strong className="si-presentation-scene-card__value">
              {mostCriticalDepartmentOverview?.name ?? data.topRisk}
            </strong>
            <p className="si-presentation-scene-card__text">
              Menor score entre os departamentos observados.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Classificação do cenário
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              {data.trendLabel} na leitura global da competência.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior peso no IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {highestWeightDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Peso atual de{" "}
              {highestWeightDepartment
                ? formatPct(highestWeightDepartment.weightInIgd)
                : "—"}{" "}
              na composição do índice.
            </p>
          </article>
        </div>

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Top 3 pesos no IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {departmentsByHighestWeight[0]?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {departmentsByHighestWeight
                .map(
                  (item) => `${item.name} (${formatPct(item.weightInIgd)})`,
                )
                .join(" • ") || "Sem dados disponíveis."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Top 3 menores scores
            </span>
            <strong className="si-presentation-scene-card__value">
              {departmentsByLowestScore[0]?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {departmentsByLowestScore
                .map((item) => `${item.name} (${formatScore(item.score)})`)
                .join(" • ") || "Sem dados disponíveis."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor momentum
            </span>
            <strong className="si-presentation-scene-card__value">
              {trendHighlightUp?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {trendHighlightUp
                ? `${trendHighlightUp.directionLabel} · atual ${formatScore(
                    trendHighlightUp.current,
                  )}`
                : "Sem destaque positivo disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior deterioração
            </span>
            <strong className="si-presentation-scene-card__value">
              {trendHighlightDown?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {trendHighlightDown
                ? `${trendHighlightDown.directionLabel} · atual ${formatScore(
                    trendHighlightDown.current,
                  )}`
                : "Sem destaque negativo disponível."}
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderDepartmentDetailScene() {
    if (!selectedDepartment) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Nenhum departamento disponível"
            description="Não há departamentos suficientes para exibir o slide detalhado."
          />
        </div>
      );
    }

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
              Slide {departmentIndex + 1} de {data?.departments.length ?? 0}
            </p>
          </div>

          <div className="si-presentation-department-slide__hero-badge">
            <span
              className={`si-status-badge si-status-badge--${getDirectionVariant(
                selectedDepartment.direction,
              )}`}
            >
              {getDirectionLabel(selectedDepartment.direction)}
            </span>
          </div>
        </section>

        <div className="si-presentation-department-slide__metrics">
          <article className="si-presentation-metric-card">
            <span>Score atual</span>
            <strong>{formatScore(selectedDepartment.score)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Período anterior</span>
            <strong>{formatScore(selectedDepartment.previous)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Contribuição no IGD</span>
            <strong>{formatScore(selectedDepartment.contribution)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Peso no IGD</span>
            <strong>{formatPct(selectedDepartment.weightInIgd)}</strong>
          </article>
        </div>

        <div className="si-presentation-department-slide__bottom">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura executiva
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartment.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartment.strategicSummary}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Agregação e direção
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartment.aggregationMode}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartment.variationLabel} ·{" "}
              {selectedDepartment.variationValue > 0 ? "+" : ""}
              {formatScore(selectedDepartment.variationValue)}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor indicador
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartmentBestIndicator?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartmentBestIndicator
                ? `Score ${formatScore(selectedDepartmentBestIndicator.score)}`
                : "Sem indicadores disponíveis."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Pior indicador
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartmentWorstIndicator?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartmentWorstIndicator
                ? `Score ${formatScore(selectedDepartmentWorstIndicator.score)}`
                : "Sem indicadores disponíveis."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Indicadores em atenção
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartmentCriticalIndicatorsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Score abaixo de 7 no conjunto atual do departamento.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Indicadores de destaque
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartmentExcellentIndicatorsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Score igual ou acima de 9 no período analisado.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Unidades consideradas
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartment.units.length}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartment.units.length > 0
                ? selectedDepartment.units
                    .slice(0, 3)
                    .map((unit) => unit.name)
                    .join(" • ")
                : "Sem detalhamento por unidade disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              3 piores indicadores
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartmentCriticalIndicatorsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              {selectedDepartmentIndicatorsSorted
                .slice(0, 3)
                .map((item) => `${item.name} (${formatScore(item.score)})`)
                .join(" • ") || "Sem indicadores disponíveis."}
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

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Alertas executivos
            </span>
            <strong className="si-presentation-scene-card__value">
              {executiveAlertsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Itens priorizados para acompanhamento direto da diretoria.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Alertas por departamento
            </span>
            <strong className="si-presentation-scene-card__value">
              {departmentAlertsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Áreas com sinais relevantes de deterioração ou atenção.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Alertas por indicador
            </span>
            <strong className="si-presentation-scene-card__value">
              {indicatorAlertsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Indicadores com comportamento abaixo da leitura esperada.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Área mais pressionada
            </span>
            <strong className="si-presentation-scene-card__value">
              {mostCriticalDepartmentOverview?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Menor score consolidado no período e maior necessidade de reação.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Principal risco executivo
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.topRisk}
            </strong>
            <p className="si-presentation-scene-card__text">
              Tema mais sensível para priorização imediata da gestão.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura do cenário
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              {data.trendLabel} no fechamento atual, com foco em correção rápida.
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderTrendScene() {
    if (!data) return null;

    const trend = data.trend;

    if (!trend) {
      return (
        <div className="si-presentation-loading-stage">
          <InfoState
            title="Tendência indisponível"
            description="Não foi possível consolidar a tendência histórica do período."
          />
        </div>
      );
    }

    return (
      <div className="si-presentation-trend-scene">
        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Período atual
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.currentPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Competência usada na leitura executiva atual.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Período anterior
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.previousPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Base usada para comparação de tendência.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Variação do IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.variationValue > 0 ? "+" : ""}
              {formatScore(data.variationValue)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Diferença consolidada entre os períodos.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Tendência
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.trendLabel}
            </strong>
            <p className="si-presentation-scene-card__text">
              Direção resumida do comportamento global.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor movimento
            </span>
            <strong className="si-presentation-scene-card__value">
              {trendHighlightUp?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {trendHighlightUp
                ? `${trendHighlightUp.directionLabel} · atual ${formatScore(
                    trendHighlightUp.current,
                  )}`
                : "Sem destaque positivo disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior queda
            </span>
            <strong className="si-presentation-scene-card__value">
              {trendHighlightDown?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {trendHighlightDown
                ? `${trendHighlightDown.directionLabel} · atual ${formatScore(
                    trendHighlightDown.current,
                  )}`
                : "Sem destaque negativo disponível."}
            </p>
          </article>
        </div>

        <div className="si-presentation-trend-scene__grid">
          {trend.igdSeries.slice(-months).map((item) => (
            <article key={item.period} className="si-presentation-scene-card">
              <span className="si-presentation-scene-card__label">
                {item.period}
              </span>
              <strong className="si-presentation-scene-card__value">
                {formatScore(item.value)}
              </strong>
              <p className="si-presentation-scene-card__text">
                {item.period === data.currentPeriod
                  ? "Competência atual em destaque na série histórica."
                  : "Série histórica do IGD no período comparado."}
              </p>
            </article>
          ))}
        </div>
      </div>
    );
  }

  function renderClosingScene() {
    if (!data) return null;

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

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Fechamento do período
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.currentPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Competência consolidada usada nesta leitura executiva.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Classificação final
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.classification}
            </strong>
            <p className="si-presentation-scene-card__text">
              Síntese da condição global do IGD no período.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Tendência observada
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.trendLabel}
            </strong>
            <p className="si-presentation-scene-card__text">
              Direção predominante do comportamento entre os períodos.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Melhor departamento
            </span>
            <strong className="si-presentation-scene-card__value">
              {mostPositiveDepartmentOverview?.name ?? data.topDepartment}
            </strong>
            <p className="si-presentation-scene-card__text">
              Melhor leitura comparativa no recorte consolidado atual.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Maior peso no IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {highestWeightDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Peso de{" "}
              {highestWeightDepartment
                ? formatPct(highestWeightDepartment.weightInIgd)
                : "—"}{" "}
              na composição do índice global.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Principal ponto de atenção
            </span>
            <strong className="si-presentation-scene-card__value">
              {weakestDepartmentCard?.name ?? data.topRisk}
            </strong>
            <p className="si-presentation-scene-card__text">
              Menor score consolidado no fechamento do período.
            </p>
          </article>
        </div>

        <div className="si-presentation-trend-scene__grid">
          {data.kpis.map((kpi) => (
            <article key={kpi.id} className="si-presentation-scene-card">
              <span className="si-presentation-scene-card__label">
                {kpi.label}
              </span>
              <strong className="si-presentation-scene-card__value">
                {kpi.value}
              </strong>
              <p className="si-presentation-scene-card__text">
                {kpi.support ?? "Síntese final da leitura executiva."}
              </p>
            </article>
          ))}
        </div>
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
      return renderOverviewScene();
    }

    if (scene === "departments") {
      return renderDepartmentsScene();
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

    return renderClosingScene();
  }

  const previousDisabled = loading || !data || scene === "overview";
  const nextDisabled =
    loading || !data || (scene === "closing" && mode === "meeting");

  return (
    <div className={`si-presentation-page si-presentation-page--${mode}`}>
      <div className="si-presentation-viewport">
        <PresentationTopBar
          competence={data?.competence ?? referenceMonth}
          sceneTitle={getSceneTitle(scene)}
          mode={mode}
          viewMode={viewMode}
          branch={branch}
          branchOptions={STRATEGIC_INDICATORS_BRANCH_OPTIONS}
          months={months}
          monthsOptions={[...PRESENTATION_MONTHS_OPTIONS]}
          isRefreshing={presentation.refreshing || presentation.loading}
          referenceMonth={referenceMonth}
          onReferenceMonthChange={handleReferenceMonthChange}
          onModeChange={handleModeChange}
          onViewModeChange={handleViewModeChange}
          onBranchChange={handleBranchChange}
          onMonthsChange={handleMonthsChange}
        />

        <div className="si-presentation-stage">
          {(presentation.error && data) || presentation.warnings.length > 0 ? (
            <div className="si-presentation-stage__feedback">
              <InfoState
                title={
                  presentation.error
                    ? "Falha ao atualizar apresentação"
                    : "Atualização parcial da apresentação"
                }
                description={
                  presentation.error ??
                  presentation.warnings.map((item) => item.message).join(" • ")
                }
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
          onPrevious={handlePrevious}
          onNext={handleNext}
          previousDisabled={previousDisabled}
          nextDisabled={nextDisabled}
        />
      </div>
    </div>
  );
}