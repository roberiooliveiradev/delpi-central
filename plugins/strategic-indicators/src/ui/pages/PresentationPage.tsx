import { useMemo, useState } from "react";
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
import { useStrategicIndicatorsAlerts } from "../../state/hooks/useStrategicIndicatorsAlerts";
import { useStrategicIndicatorsExecutiveSummary } from "../../state/hooks/useStrategicIndicatorsExecutiveSummary";
import { buildPresentationViewData } from "../../data/types/presentation";

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

export function PresentationPage({ getAccessToken }: PresentationPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());
  const [mode, setMode] = useState<PresentationMode>("meeting");
  const [scene, setScene] = useState<PresentationScene>("overview");
  const [departmentIndex, setDepartmentIndex] = useState(0);

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const executive = useStrategicIndicatorsExecutiveSummary({
    competence: referenceMonth,
    startDate,
    endDate,
    getAccessToken,
  });

  const alerts = useStrategicIndicatorsAlerts({
    competence: referenceMonth,
    startDate,
    endDate,
    getAccessToken,
  });

  const loading =
    (executive.loading && !executive.data) || (alerts.loading && !alerts.data);

  const hardError =
    !loading && (executive.error ?? alerts.error) && (!executive.data || !alerts.data);

  const data =
    executive.data && alerts.data
      ? buildPresentationViewData({
          executiveSummary: executive.data,
          executiveAlerts: alerts.data.executiveAlerts,
        })
      : null;

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

    const variation = selectedDepartment.current - selectedDepartment.previous;

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
            <StatusBadge
              label={
                selectedDepartment.direction === "up"
                  ? "Melhora"
                  : selectedDepartment.direction === "down"
                    ? "Queda"
                    : "Estável"
              }
              variant={
                selectedDepartment.direction === "up"
                  ? "success"
                  : selectedDepartment.direction === "down"
                    ? "warning"
                    : "neutral"
              }
            />
          </div>
        </section>

        <div className="si-presentation-department-slide__metrics">
          <article className="si-presentation-metric-card">
            <span>Score atual</span>
            <strong>{selectedDepartment.current.toFixed(1)}</strong>
          </article>

          <article className="si-presentation-metric-card">
            <span>Período anterior</span>
            <strong>{selectedDepartment.previous.toFixed(1)}</strong>
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
            <strong>
              {selectedDepartment.direction === "up"
                ? "Melhora"
                : selectedDepartment.direction === "down"
                  ? "Queda"
                  : "Estável"}
            </strong>
          </article>
        </div>

        <div className="si-presentation-department-slide__bottom">
          <article className="si-presentation-scene-card">
            <span className="si-presentation-scene-card__label">
              Leitura executiva
            </span>
            <strong className="si-presentation-scene-card__value">
              {selectedDepartment.name}
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
              executive.error ?? alerts.error ?? "Não foi possível obter os dados necessários."
            }
            actionLabel="Tentar novamente"
            onAction={() => {
              void executive.reload();
              void alerts.reload();
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
      return renderDepartmentDetailScene();
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
          isRefreshing={executive.refreshing || alerts.refreshing || loading}
          referenceMonth={referenceMonth}
          onReferenceMonthChange={setReferenceMonth}
          onModeChange={setMode}
        />

        <div className="si-presentation-stage">
          {executive.error && executive.data && alerts.data ? (
            <div className="si-presentation-stage__feedback">
              <InfoState
                title="Falha ao atualizar apresentação"
                description={executive.error}
                actionLabel="Tentar novamente"
                onAction={() => {
                  void executive.reload();
                  void alerts.reload();
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