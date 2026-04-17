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
import type { PresentationDepartmentBoardItem } from "../../data/types/presentation";
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

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(
    getCurrentStrategicIndicatorsMonthValue(),
  );
  const [mode, setMode] = useState<PresentationMode>("meeting");
  const [viewMode, setViewMode] =
    useState<StrategicIndicatorsViewMode>("consolidated");
  const [branch, setBranch] = useState("01");
  const [scene, setScene] = useState<PresentationScene>("overview");
  const [departmentIndex, setDepartmentIndex] = useState(0);

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
    months: 3,
    getAccessToken,
  });

  const data = presentation.data;
  const loading = presentation.loading;
  const hardError = !loading && (!data || Boolean(presentation.error));

  useEffect(() => {
    setDepartmentIndex(0);
    presentation.setFocusedDepartmentId(null);
  }, [viewMode, branch, referenceMonth]);

  useEffect(() => {
    if (!presentation.departmentIds.length) {
      return;
    }

    const nextDepartmentId =
      presentation.departmentIds[departmentIndex] ??
      presentation.departmentIds[0] ??
      null;

    presentation.setFocusedDepartmentId(nextDepartmentId);
  }, [departmentIndex, presentation.departmentIds, presentation.setFocusedDepartmentId]);

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
  const selectedDepartment =
    data?.departments[departmentIndex] ?? data?.departments[0] ?? null;

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
    }
  }

  function renderDepartmentDetailScene(
    department: PresentationDepartmentBoardItem | null,
  ) {
    if (!department) {
      return (
        <div className="si-presentation-scene-card">
          <InfoState
            title="Nenhum departamento disponível"
            description="Não há departamentos suficientes para exibir o slide detalhado."
          />
        </div>
      );
    }

    const variation = department.current - department.previous;

    return (
      <div className="si-presentation-department-slide">
        <section className="si-presentation-department-slide__hero">
          <div className="si-presentation-department-slide__hero-main">
            <span className="si-presentation-department-slide__eyebrow">
              Departamento em foco
            </span>
            <h2 className="si-presentation-department-slide__title">
              {department.name}
            </h2>
            <p className="si-presentation-department-slide__subtitle">
              Slide {departmentIndex + 1} de {data?.departments.length ?? 0}
            </p>
          </div>

          <div className="si-presentation-department-slide__hero-badge">
            <span
              className={`si-status-badge si-status-badge--${getDirectionVariant(
                department.direction,
              )}`}
            >
              {getDirectionLabel(department.direction)}
            </span>
          </div>
        </section>

        <div className="si-presentation-department-slide__metrics">
          <article className="si-presentation-metric-card">
            <span>Score atual</span>
            <strong>{department.current.toFixed(1)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Período anterior</span>
            <strong>{department.previous.toFixed(1)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Variação</span>
            <strong>
              {variation > 0 ? "+" : ""}
              {variation.toFixed(1)}
            </strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Direção</span>
            <strong>{getDirectionLabel(department.direction)}</strong>
          </article>
        </div>

        <div className="si-presentation-department-slide__bottom">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura executiva
            </span>
            <strong className="si-presentation-scene-card__value">
              {department.name}
            </strong>
            <p className="si-presentation-scene-card__text">
              Departamento em evidência para aprofundamento executivo no período.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Principal mensagem
            </span>
            <strong className="si-presentation-scene-card__value">
              {variation > 0
                ? "Evolução positiva"
                : variation < 0
                  ? "Exige atenção"
                  : "Estabilidade"}
            </strong>
            <p className="si-presentation-scene-card__text">
              Comparativo direto com o período anterior para orientar a reunião.
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderTrendScene() {
    if (!data) return null;

    return (
      <div className="si-presentation-trend-scene">
        <div className="si-presentation-trend-scene__grid">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">Período atual</span>
            <strong className="si-presentation-scene-card__value">
              {data.currentPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Competência usada na leitura executiva atual.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">Período anterior</span>
            <strong className="si-presentation-scene-card__value">
              {data.previousPeriod}
            </strong>
            <p className="si-presentation-scene-card__text">
              Base usada para comparação de tendência.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">Variação do IGD</span>
            <strong className="si-presentation-scene-card__value">
              {data.variationValue > 0 ? "+" : ""}
              {data.variationValue.toFixed(1)}
            </strong>
            <p className="si-presentation-scene-card__text">
              Diferença consolidada entre os períodos.
            </p>
          </article>

          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">Tendência</span>
            <strong className="si-presentation-scene-card__value">
              {data.trendLabel}
            </strong>
            <p className="si-presentation-scene-card__text">
              Direção resumida do comportamento global.
            </p>
          </article>
        </div>
      </div>
    );
  }

  function renderScene() {
    if (loading) {
      return (
        <div className="si-presentation-loading-stage">
          <InfoState
            title="Carregando apresentação"
            description="Aguarde enquanto a síntese executiva é preparada."
          />
        </div>
      );
    }

    if (hardError || !data) {
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
          <PresentationDepartmentBoard departments={data.departments.slice(0, 6)} />
        </div>
      );
    }

    if (scene === "department_detail") {
      return renderDepartmentDetailScene(selectedDepartment);
    }

    if (scene === "alerts") {
      return (
        <div className="si-presentation-single-scene">
          <PresentationAlertsBoard alerts={data.executiveAlerts.slice(0, 3)} />
        </div>
      );
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

  const previousDisabled = loading || !data || scene === "overview";
  const nextDisabled = loading || !data || scene === "closing";

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
          isRefreshing={presentation.refreshing || presentation.loading}
          referenceMonth={referenceMonth}
          onReferenceMonthChange={setReferenceMonth}
          onModeChange={setMode}
          onViewModeChange={setViewMode}
          onBranchChange={setBranch}
        />

        <div className="si-presentation-stage">
          {presentation.error && data ? (
            <div className="si-presentation-stage__feedback">
              <InfoState
                title="Falha ao atualizar apresentação"
                description={presentation.error}
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