import { useEffect, useMemo, useState } from "react";

import { parseRoute } from "../constants/actionPlans";
import { DashboardPage } from "./DashboardPage";
import { OverduePage } from "./OverduePage";
import { PlanDetailPage } from "./PlanDetailPage";
import { PlanFormPage } from "./PlanFormPage";
import { PlansListPage } from "./PlansListPage";
import { RecurrencePage } from "./RecurrencePage";
import { SolutionPatternsPage } from "./SolutionPatternsPage";

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
    const next = parseRoute(path);
    setView(next.view);
    setPlanId(next.planId);
  }

  if (view === "detail" && planId) {
    return <PlanDetailPage planId={planId} onNavigate={handleNavigate} />;
  }

  if (view === "new") {
    return <PlanFormPage onNavigate={handleNavigate} />;
  }

  if (view === "list") {
    return <PlansListPage onNavigate={handleNavigate} />;
  }

  if (view === "overdue") {
    return <OverduePage onNavigate={handleNavigate} />;
  }

  if (view === "recurrence") {
    return <RecurrencePage onNavigate={handleNavigate} />;
  }

  if (view === "solutions") {
    return <SolutionPatternsPage onNavigate={handleNavigate} />;
  }

  return <DashboardPage onNavigate={handleNavigate} />;
}
