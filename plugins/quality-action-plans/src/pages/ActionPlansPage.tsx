import { useEffect, useMemo, useState } from "react";

import { parseRoute } from "../constants/actionPlans";
import { navigatePac } from "../utils/navigation";
import { DashboardPage } from "./DashboardPage";
import { MyQueuePage } from "./MyQueuePage";
import { OverduePage } from "./OverduePage";
import { PlanDetailPage } from "./PlanDetailPage";
import { PlanFormPage } from "./PlanFormPage";
import { PlansListPage } from "./PlansListPage";
import { RecurrencePage } from "./RecurrencePage";
import { SolutionPatternsPage } from "./SolutionPatternsPage";
import { EffectivenessPendingPage } from "./EffectivenessPendingPage";
import { EvidencesSearchPage } from "./EvidencesSearchPage";
import { PacPermissionsProvider } from "../context/PacPermissionsContext";

type Props = {
  pathname?: string;
};

export function ActionPlansPage({ pathname }: Props) {
  const externalRoute = useMemo(() => parseRoute(pathname), [pathname]);
  const [view, setView] = useState(externalRoute.view);
  const [planId, setPlanId] = useState<string | undefined>(externalRoute.planId);

  useEffect(() => {
    setView(externalRoute.view);
    setPlanId(externalRoute.planId);
  }, [externalRoute.view, externalRoute.planId]);

  function handleNavigate(path: string) {
    navigatePac(path);
    const next = parseRoute(path);
    setView(next.view);
    setPlanId(next.planId);
  }

  let page = <DashboardPage onNavigate={handleNavigate} />;

  if (view === "detail" && planId) {
    page = <PlanDetailPage planId={planId} onNavigate={handleNavigate} />;
  } else if (view === "new") {
    page = <PlanFormPage onNavigate={handleNavigate} />;
  } else if (view === "list") {
    page = <PlansListPage onNavigate={handleNavigate} />;
  } else if (view === "overdue") {
    page = <OverduePage onNavigate={handleNavigate} />;
  } else if (view === "my-queue") {
    page = <MyQueuePage onNavigate={handleNavigate} />;
  } else if (view === "effectiveness-pending") {
    page = <EffectivenessPendingPage onNavigate={handleNavigate} />;
  } else if (view === "recurrence") {
    page = <RecurrencePage onNavigate={handleNavigate} />;
  } else if (view === "solutions") {
    page = <SolutionPatternsPage onNavigate={handleNavigate} />;
  } else if (view === "evidences") {
    page = <EvidencesSearchPage onNavigate={handleNavigate} />;
  }

  return <PacPermissionsProvider>{page}</PacPermissionsProvider>;
}
