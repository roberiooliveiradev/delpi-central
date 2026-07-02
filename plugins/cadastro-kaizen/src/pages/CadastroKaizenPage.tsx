import { useEffect, useMemo, useState } from "react";

import { detailPath, parseRoute, type View } from "../constants/kaizen";
import { navigateKaizen } from "../utils/navigation";
import { KaizenDashboardPage } from "./KaizenDashboardPage";
import { KaizenDetailPage } from "./KaizenDetailPage";
import { KaizenFormPage } from "./KaizenFormPage";
import { KaizenListPage } from "./KaizenListPage";

type Props = {
  pathname?: string;
};

export function CadastroKaizenPage({ pathname }: Props) {
  const externalRoute = useMemo(() => parseRoute(pathname), [pathname]);
  const [view, setView] = useState<View>(externalRoute.view);
  const [recordId, setRecordId] = useState<string | undefined>(externalRoute.id);

  useEffect(() => {
    setView(externalRoute.view);
    setRecordId(externalRoute.id);
  }, [externalRoute.view, externalRoute.id]);

  function handleNavigate(path: string) {
    navigateKaizen(path);
    const next = parseRoute(path);
    setView(next.view);
    setRecordId(next.id);
  }

  if (view === "dashboard") {
    return <KaizenDashboardPage onNavigate={handleNavigate} />;
  }

  if (view === "new") {
    return (
      <KaizenFormPage
        mode="new"
        onNavigate={handleNavigate}
        onCreated={(id) => handleNavigate(detailPath(id))}
      />
    );
  }

  if ((view === "detail" || view === "edit") && recordId) {
    return <KaizenDetailPage recordId={recordId} onNavigate={handleNavigate} />;
  }

  return <KaizenListPage onNavigate={handleNavigate} />;
}
