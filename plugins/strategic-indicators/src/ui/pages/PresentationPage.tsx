import { alertsMock } from "../../data/mocks/alertsMock";
import { executiveDashboardMock } from "../../data/mocks/executiveDashboardMock";
import { trendsMock } from "../../data/mocks/trendsMock";
import { PresentationAlertsBoard } from "../components/PresentationAlertsBoard";
import { PresentationClosingPanel } from "../components/PresentationClosingPanel";
import { PresentationDepartmentBoard } from "../components/PresentationDepartmentBoard";
import { PresentationExecutiveStrip } from "../components/PresentationExecutiveStrip";
import { PresentationHero } from "../components/PresentationHero";
import { PresentationNarrativeStrip } from "../components/PresentationNarrativeStrip";

export function PresentationPage() {
  const bestDepartment = [...executiveDashboardMock.departments].sort(
    (a, b) => b.score - a.score
  )[0];

  const topRiskDepartment = alertsMock.departmentAlerts[0];

  const trendLabel =
    trendsMock.currentIgd > trendsMock.previousIgd
      ? "Melhora no período"
      : trendsMock.currentIgd < trendsMock.previousIgd
        ? "Queda no período"
        : "Estabilidade no período";

  const currentPeriod =
    trendsMock.igdSeries[trendsMock.igdSeries.length - 1]?.period ?? "Atual";
  const previousPeriod =
    trendsMock.igdSeries[trendsMock.igdSeries.length - 2]?.period ?? "Anterior";

  return (
    <div className="si-presentation-page">
      <PresentationHero
        igd={executiveDashboardMock.igd}
        classification={executiveDashboardMock.classification}
        trendLabel={trendLabel}
      />

      <PresentationNarrativeStrip
        classification={executiveDashboardMock.classification}
        trendLabel={trendLabel}
        topDepartment={bestDepartment?.name ?? "—"}
        topRisk={topRiskDepartment?.departmentName ?? "—"}
      />

      <PresentationExecutiveStrip
        currentIgd={trendsMock.currentIgd}
        previousIgd={trendsMock.previousIgd}
        topDepartment={bestDepartment?.name ?? "—"}
        topRisk={topRiskDepartment?.departmentName ?? "—"}
      />

      <div className="si-presentation-layout">
        <PresentationDepartmentBoard departments={trendsMock.departments} />
        <PresentationAlertsBoard alerts={alertsMock.executiveAlerts} />
      </div>

      <PresentationClosingPanel
        currentPeriod={currentPeriod}
        previousPeriod={previousPeriod}
        classification={executiveDashboardMock.classification}
        trendLabel={trendLabel}
        topDepartment={bestDepartment?.name ?? "—"}
        topRisk={topRiskDepartment?.departmentName ?? "—"}
      />
    </div>
  );
}