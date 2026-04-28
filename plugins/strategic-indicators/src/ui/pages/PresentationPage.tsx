import { useEffect, useMemo, useRef, useState } from "react";
import { PresentationAlertsBoard } from "../components/PresentationAlertsBoard";
import { PresentationClosingPanel } from "../components/PresentationClosingPanel";
import { PresentationDepartmentBoard } from "../components/PresentationDepartmentBoard";
import { PresentationDepartmentSlideScene } from "../components/PresentationDepartmentSlideScene";
import { PresentationEdgeNavigation } from "../components/PresentationEdgeNavigation";
import { PresentationHero } from "../components/PresentationHero";
import { PresentationNarrativeStrip } from "../components/PresentationNarrativeStrip";
import { PresentationTopBar } from "../components/PresentationTopBar";
import { InfoState } from "../components/InfoState";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { PresentationAlertsSeverityDonut } from "../components/PresentationAlertsSeverityDonut";
import { PresentationTrendAreaChart } from "../components/PresentationTrendAreaChart";
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

function getSceneRenderKey(
  scene: PresentationScene,
  departmentIndex: number,
): string {
  if (scene === "department_detail") {
    return `${scene}-${departmentIndex}`;
  }

  return scene;
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

  if (mode === "tv") return base;
  if (mode === "slide") return base + 2000;
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
    return base + Math.min(criticalIndicatorsCount, 6) * 1000;
  }

  if (scene === "alerts") {
    const totalAlerts =
      executiveAlertsCount + departmentAlertsCount + indicatorAlertsCount;
    return base + Math.min(totalAlerts, 8) * 500;
  }

  if (scene === "trend") {
    return base + Math.min(trendPointsCount, 6) * 400;
  }

  return base;
}

function getDirectionLabel(direction: "up" | "down" | "stable") {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
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

  return [3, 6, 12].includes(parsedValue) ? parsedValue : 3;
}

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [isFullscreen, setIsFullscreen] = useState<boolean>(() => {
    if (typeof document === "undefined") return false;
    return Boolean(document.fullscreenElement);
  });
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
  
  const touchStartXRef = useRef<number | null>(null);
  const touchStartYRef = useRef<number | null>(null);

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

  function syncDeckAfterFilterChange() {
    if (scene === "department_detail") {
      setDepartmentIndex(0);
      presentation.setFocusedDepartmentId(null);
    }
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

  useEffect(() => {
    return () => {
      clearAutoplayResumeTimer();
    };
  }, []);

  useEffect(() => {
    syncDeckAfterFilterChange();
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

  async function handleToggleFullscreen() {
    try {
      if (typeof document === "undefined") return;

      if (document.fullscreenElement) {
        await document.exitFullscreen();
        return;
      }

      await document.documentElement.requestFullscreen();
    } catch {
      // fullscreen pode falhar por política do navegador
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

  function handleSceneTouchStart(event: React.TouchEvent<HTMLDivElement>) {
    if (event.touches.length !== 1) return;

    const touch = event.touches[0];
    touchStartXRef.current = touch.clientX;
    touchStartYRef.current = touch.clientY;
  }

  function handleSceneTouchEnd(event: React.TouchEvent<HTMLDivElement>) {
    if (touchStartXRef.current === null || touchStartYRef.current === null) {
      return;
    }

    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - touchStartXRef.current;
    const deltaY = touch.clientY - touchStartYRef.current;

    touchStartXRef.current = null;
    touchStartYRef.current = null;

    const minSwipeDistance = 64;
    const horizontalDominance = Math.abs(deltaX) > Math.abs(deltaY) * 1.25;

    if (!horizontalDominance || Math.abs(deltaX) < minSwipeDistance) {
      return;
    }

    if (deltaX > 0) {
      handlePrevious();
      return;
    }

    handleNext();
  }
  function handleModeChange(nextMode: PresentationMode) {
    pauseAutoplayTemporarily();
    setMode(nextMode);
  }

  function handleViewModeChange(nextViewMode: StrategicIndicatorsViewMode) {
    pauseAutoplayTemporarily();
    setViewMode(nextViewMode);
  }

  function handleBranchChange(nextBranch: string) {
    pauseAutoplayTemporarily();
    setBranch(nextBranch);
  }

  function handleReferenceMonthChange(nextReferenceMonth: string) {
    pauseAutoplayTemporarily();
    setReferenceMonth(nextReferenceMonth);
  }

  function handleMonthsChange(nextMonths: number) {
    pauseAutoplayTemporarily();
    setMonths(nextMonths);
  }

  const selectedBoardDepartment =
    data?.departments[departmentIndex] ?? data?.departments[0] ?? null;

  const departmentFocus =
    data?.departmentFocus &&
    selectedBoardDepartment &&
    data.departmentFocus.id === selectedBoardDepartment.id
      ? data.departmentFocus
      : null;

  const mostCriticalDepartmentOverview = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)[0];

  const mostPositiveDepartmentOverview = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.score - a.score)[0];

  const departmentsByLowestScore = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)
    .slice(0, 3);

  const departmentsByHighestContribution = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3);

  const strongestDepartmentCard = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.score - a.score)[0];

  const weakestDepartmentCard = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => a.score - b.score)[0];

  const highestContributionDepartment = [...(data?.departmentsOverview ?? [])]
    .sort((a, b) => b.contribution - a.contribution)[0];

  const trendHighlightUp = [...(data?.trend?.departments ?? [])].sort(
    (a, b) => b.current - b.previous - (a.current - a.previous),
  )[0];

  const trendHighlightDown = [...(data?.trend?.departments ?? [])].sort(
    (a, b) => a.current - a.previous - (b.current - b.previous),
  )[0];

  const executiveAlertsCount = data?.alerts.executive.length ?? 0;
  const departmentAlertsCount = data?.alerts.departments.length ?? 0;
  const indicatorAlertsCount = data?.alerts.indicators.length ?? 0;

  const selectedDepartmentCriticalIndicatorsCount =
    departmentFocus?.indicators.filter((item) => item.score < 7).length ?? 0;

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
    function handleFullscreenChange() {
      setIsFullscreen(Boolean(document.fullscreenElement));
    }

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

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
    function isTypingTarget(target: EventTarget | null) {
      if (!(target instanceof HTMLElement)) return false;

      const tagName = target.tagName.toLowerCase();

      return (
        tagName === "input" ||
        tagName === "textarea" ||
        tagName === "select" ||
        target.isContentEditable
      );
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (isTypingTarget(event.target)) {
        return;
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        pauseAutoplayTemporarily();
        goToPrevious();
        return;
      }

      if (event.key === "ArrowRight") {
        event.preventDefault();
        pauseAutoplayTemporarily();
        goToNext();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goToNext, goToPrevious, pauseAutoplayTemporarily]);

  function renderOverviewScene() {
    if (!data) return null;

    const bestDepartmentName =
      strongestDepartmentCard?.name ??
      mostPositiveDepartmentOverview?.name ??
      data.topDepartment;

    const primaryRiskName =
      weakestDepartmentCard?.name ??
      mostCriticalDepartmentOverview?.name ??
      data.topRisk;

    return (
      <div className="si-presentation-overview-scene">
        <PresentationHero
          igd={data.igd}
          classification={data.classification}
          trendLabel={data.trendLabel}
          bestDepartment={bestDepartmentName}
          primaryRisk={primaryRiskName}
        />

        <PresentationNarrativeStrip
          classification={data.classification}
          trendLabel={data.trendLabel}
          highlightedDepartment={bestDepartmentName}
          riskLabel={primaryRiskName}
        />
      </div>
    );
  }

  function renderDepartmentsScene() {
    if (!data) return null;

    return (
      <div className="si-presentation-single-scene">
        <PresentationDepartmentBoard
          departments={data.departmentsOverview}
          trendDepartments={data.trend?.departments}
        />

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
              Maior contribuição
            </span>
            <strong className="si-presentation-scene-card__value">
              {highestContributionDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Contribuição atual de{" "}
              {highestContributionDepartment
                ? formatScore(highestContributionDepartment.contribution)
                : "—"}{" "}
              no IGD.
            </p>
          </article>
        </div>

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Top 3 contribuições
            </span>
            <strong className="si-presentation-scene-card__value">
              {departmentsByHighestContribution[0]?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {departmentsByHighestContribution
                .map((item) => `${item.name} (${formatScore(item.contribution)})`)
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
                ? `${getDirectionLabel(trendHighlightUp.direction)} · atual ${formatScore(
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
                ? `${getDirectionLabel(trendHighlightDown.direction)} · atual ${formatScore(
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
    return (
      <PresentationDepartmentSlideScene
        department={departmentFocus}
        series={departmentFocus?.series}
        mode={mode}
        competence={referenceMonth}
      />
    );
  }

  function renderAlertsScene() {
    if (!data) return null;

    const alertsToShow =
      data.alerts.executive.length > 0
        ? data.alerts.executive
        : data.executiveAlerts;

    const severityTotals = {
      high:
        data.alerts.executive.filter((item) => item.severity === "high").length +
        data.alerts.departments.filter((item) => item.severity === "high").length +
        data.alerts.indicators.filter((item) => item.severity === "high").length,
      medium:
        data.alerts.executive.filter((item) => item.severity === "medium").length +
        data.alerts.departments.filter((item) => item.severity === "medium").length +
        data.alerts.indicators.filter((item) => item.severity === "medium").length,
      low:
        data.alerts.executive.filter((item) => item.severity === "low").length +
        data.alerts.departments.filter((item) => item.severity === "low").length +
        data.alerts.indicators.filter((item) => item.severity === "low").length,
    };

    const topIndicatorAlert = [...data.alerts.indicators].sort(
      (a, b) => a.simulatedScore - b.simulatedScore,
    )[0];

    const priorityRecommendation =
      alertsToShow[0]?.recommendation ??
      topIndicatorAlert?.recommendation ??
      "Priorizar resposta rápida para os pontos críticos do período.";

    return (
      <div className="si-presentation-alerts-scene">
        <div className="si-presentation-alerts-scene__top">
          <PresentationAlertsSeverityDonut values={severityTotals} />

          <PresentationAlertsBoard alerts={alertsToShow} />
        </div>

        <div className="si-presentation-alerts-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Alertas executivos
            </span>
            <strong className="si-presentation-scene-card__value">
              {executiveAlertsCount}
            </strong>
            <p className="si-presentation-scene-card__text">
              Itens priorizados para leitura direta da diretoria.
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
              Áreas que exigem acompanhamento executivo imediato.
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
              Indicadores com score abaixo da leitura esperada.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Departamento mais pressionado
            </span>
            <strong className="si-presentation-scene-card__value">
              {mostCriticalDepartmentOverview?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Menor score consolidado do período.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Indicador mais crítico
            </span>
            <strong className="si-presentation-scene-card__value">
              {topIndicatorAlert?.indicatorName ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {topIndicatorAlert?.departmentName
                ? `Área: ${topIndicatorAlert.departmentName}`
                : "Sem indicador crítico disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Recomendação prioritária
            </span>
            <strong className="si-presentation-scene-card__value">
              Ação imediata
            </strong>
            <p className="si-presentation-scene-card__text">
              {priorityRecommendation}
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

    const igdSeries = trend.igdSeries.slice(-months);

    const strongestMomentumDepartment = [...trend.departments].sort(
      (a, b) => b.netVariation - a.netVariation,
    )[0] ?? null;

    const biggestDropDepartment = [...trend.departments].sort(
      (a, b) => a.netVariation - b.netVariation,
    )[0] ?? null;

    const bestCurrentDepartment = [...trend.departments].sort(
      (a, b) => b.current - a.current,
    )[0] ?? null;

    const worstCurrentDepartment = [...trend.departments].sort(
      (a, b) => a.current - b.current,
    )[0] ?? null;

    const currentIgd = trend.currentIgd ?? data.igd ?? 0;
    const previousIgd = trend.previousIgd ?? currentIgd;
    const igdDelta = currentIgd - previousIgd;

    const trendSummaryLabel =
      igdDelta > 0.09
        ? "Trajetória de melhora no fechamento atual."
        : igdDelta < -0.09
          ? "Trajetória de queda no fechamento atual."
          : "Comportamento estável entre os períodos recentes.";

    return (
      <div className="si-presentation-trend-scene">
        <div className="si-presentation-trend-scene__hero">
          <section className="si-presentation-trend-scene__chart-card">
            <div className="si-presentation-trend-scene__chart-header">
              <div className="si-presentation-trend-scene__chart-header-copy">
                <span className="si-presentation-trend-scene__chart-eyebrow">
                  Evolução histórica
                </span>
                <h3 className="si-presentation-trend-scene__chart-title">
                  Comportamento do IGD nos últimos {months} meses
                </h3>
                <p className="si-presentation-trend-scene__chart-subtitle">
                  Leitura consolidada da trajetória do índice global no recorte
                  selecionado.
                </p>
              </div>

              <div className="si-presentation-trend-scene__chart-highlight">
                <span>IGD atual</span>
                <strong>{formatScore(currentIgd)}</strong>
              </div>
            </div>

            <div className="si-presentation-trend-scene__chart">
              <PresentationTrendAreaChart points={igdSeries} />
            </div>
          </section>
        </div>

        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card si-presentation-scene-card--primary">
            <span className="si-presentation-scene-card__label">Período atual</span>
            <strong className="si-presentation-scene-card__value">
              {data.currentPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Competência usada na leitura executiva atual.
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--secondary">
            <span className="si-presentation-scene-card__label">
              Período anterior
            </span>
            <strong className="si-presentation-scene-card__value">
              {data.previousPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Base de comparação imediata do índice global.
            </p>
          </article>

          <article
            className={`si-presentation-scene-card ${
              igdDelta >= 0
                ? "si-presentation-scene-card--success"
                : "si-presentation-scene-card--danger"
            }`}
          >
            <span className="si-presentation-scene-card__label">
              Variação do IGD
            </span>
            <strong className="si-presentation-scene-card__value">
              {igdDelta > 0 ? "+" : ""}
              {formatScore(igdDelta)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Diferença consolidada entre o fechamento atual e o anterior.
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--warning">
            <span className="si-presentation-scene-card__label">Tendência</span>
            <strong className="si-presentation-scene-card__value">
              {data.trendLabel}
            </strong>
            <p className="si-presentation-scene-card__text">
              {trendSummaryLabel}
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--success">
            <span className="si-presentation-scene-card__label">
              Melhor movimento
            </span>
            <strong className="si-presentation-scene-card__value">
              {strongestMomentumDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {strongestMomentumDepartment
                ? `Variação acumulada de ${
                    strongestMomentumDepartment.netVariation > 0 ? "+" : ""
                  }${formatScore(strongestMomentumDepartment.netVariation)}.`
                : "Sem destaque positivo disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--danger">
            <span className="si-presentation-scene-card__label">Maior queda</span>
            <strong className="si-presentation-scene-card__value">
              {biggestDropDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {biggestDropDepartment
                ? `Variação acumulada de ${formatScore(
                    biggestDropDepartment.netVariation,
                  )}.`
                : "Sem destaque negativo disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--success">
            <span className="si-presentation-scene-card__label">
              Melhor score atual
            </span>
            <strong className="si-presentation-scene-card__value">
              {bestCurrentDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {bestCurrentDepartment
                ? `Score atual de ${formatScore(bestCurrentDepartment.current)}.`
                : "Sem referência disponível."}
            </p>
          </article>

          <article className="si-presentation-scene-card si-presentation-scene-card--danger">
            <span className="si-presentation-scene-card__label">
              Menor score atual
            </span>
            <strong className="si-presentation-scene-card__value">
              {worstCurrentDepartment?.name ?? "—"}
            </strong>
            <p className="si-presentation-scene-card__text">
              {worstCurrentDepartment
                ? `Score atual de ${formatScore(worstCurrentDepartment.current)}.`
                : "Sem referência disponível."}
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderClosingScene() {
    if (!data) return null;

    const recommendation =
      data.executiveAlerts[0]?.recommendation ??
      "Sem recomendação executiva disponível.";

    const strongestDepartmentName =
      mostPositiveDepartmentOverview?.name ?? data.topDepartment;

    const highestContributionName =
      highestContributionDepartment?.name ?? strongestDepartmentName;

    const immediateFocusName =
      weakestDepartmentCard?.name ?? data.topRisk;

    const cycleMovementValue = trendHighlightUp?.name ?? "—";
    const cycleMovementSupport = trendHighlightUp
      ? `Score atual ${formatScore(trendHighlightUp.current)}`
      : "Sem destaque adicional disponível.";

    const reinforcementCards = [
      {
        label: "Departamento de destaque",
        value: strongestDepartmentName,
        text:
          data.topDepartment === strongestDepartmentName
            ? "Melhor leitura comparativa no recorte atual."
            : `Destaque executivo do período: ${data.topDepartment}.`,
      },
      {
        label: "Foco imediato",
        value: immediateFocusName,
        text: recommendation,
      },
      {
        label: "Maior contribuição",
        value: highestContributionName,
        text: highestContributionDepartment
          ? `Contribuição atual de ${formatScore(
              highestContributionDepartment.contribution,
            )} no IGD.`
          : "Sem contribuição consolidada disponível.",
      },
      {
        label: "Movimento do ciclo",
        value: cycleMovementValue,
        text: cycleMovementSupport,
      },
    ];

    const footerCards = [
      {
        label: "Próximo passo",
        value: data.executiveAlerts[0]?.title ?? "Plano executivo",
        text: recommendation,
      },
      {
        label: "Risco prioritário",
        value: data.topRisk,
        text: weakestDepartmentCard
          ? `${weakestDepartmentCard.name} fecha o período com score ${formatScore(
              weakestDepartmentCard.score,
            )}.`
          : "Tema mais sensível para acompanhamento imediato.",
      },
      {
        label: "Mensagem de encerramento",
        value: data.classification,
        text: `${data.trendLabel} no fechamento entre ${data.previousPeriod} e ${data.currentPeriod}.`,
      },
    ];

    return (
      <div className="si-presentation-single-scene">
        <PresentationClosingPanel
          currentPeriod={data.currentPeriod}
          previousPeriod={data.previousPeriod}
          classification={data.classification}
          trendLabel={data.trendLabel}
          topDepartment={strongestDepartmentName}
          topRisk={data.topRisk}
          igd={data.igd}
          recommendation={recommendation}
        />

        <div className="si-presentation-closing__reinforcement-grid">
          {reinforcementCards.map((card) => (
            <article key={card.label} className="si-presentation-scene-card">
              <span className="si-presentation-scene-card__label">
                {card.label}
              </span>
              <strong className="si-presentation-scene-card__value">
                {card.value}
              </strong>
              <p className="si-presentation-scene-card__text">{card.text}</p>
            </article>
          ))}
        </div>

        <div className="si-presentation-closing__footer-grid">
          {footerCards.map((card) => (
            <article key={card.label} className="si-presentation-scene-card">
              <span className="si-presentation-scene-card__label">
                {card.label}
              </span>
              <strong className="si-presentation-scene-card__value">
                {card.value}
              </strong>
              <p className="si-presentation-scene-card__text">{card.text}</p>
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
          <LoadingActivityInline
            title="Carregando apresentação"
            description="Aguarde enquanto a visão executiva do IGD e dos departamentos é preparada."
            variant="panel"
            tone="info"
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

    if (scene === "overview") return renderOverviewScene();
    if (scene === "departments") return renderDepartmentsScene();
    if (scene === "department_detail") return renderDepartmentDetailScene();
    if (scene === "alerts") return renderAlertsScene();
    if (scene === "trend") return renderTrendScene();
    return renderClosingScene();
  }

  const previousDisabled = loading || !data || scene === "overview";
  const nextDisabled =
    loading || !data || (scene === "closing" && mode === "meeting");

  const sceneRenderKey = getSceneRenderKey(scene, departmentIndex);
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
          isFullscreen={isFullscreen}
          onToggleFullscreen={handleToggleFullscreen}
        />

        <div className="si-presentation-stage">
          {(presentation.error && data) || presentation.warnings.length > 0 ? (
            <div className="si-presentation-stage__feedback">
              {presentation.error ? (
                <InfoState
                  title="Falha ao atualizar apresentação"
                  description={presentation.error}
                  actionLabel="Tentar novamente"
                  onAction={() => {
                    void presentation.reload();
                  }}
                />
              ) : (
                <LoadingActivityInline
                  title="Atualização parcial da apresentação"
                  description={presentation.warnings
                    .map((item) => item.message)
                    .join(" • ")}
                  variant="compact"
                  tone="info"
                />
              )}
            </div>
          ) : null}

          <div
            className="si-presentation-scene-frame"
            onTouchStart={handleSceneTouchStart}
            onTouchEnd={handleSceneTouchEnd}
          >
            <div
              key={sceneRenderKey}
              className="si-presentation-scene-frame__content"
            >
              {renderScene()}
            </div>
          </div>
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