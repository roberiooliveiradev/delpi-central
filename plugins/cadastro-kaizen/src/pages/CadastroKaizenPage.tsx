import { useEffect, useMemo, useState } from "react";

import {
  dashboardPath,
  detailPath,
  listPath,
  newPath,
  parseRoute,
  type View,
} from "../constants/kaizen";
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
    if (path === dashboardPath()) {
      setView("dashboard");
      setRecordId(undefined);
      return;
    }
    if (path === listPath()) {
      setView("list");
      setRecordId(undefined);
      return;
    }
    if (path === newPath()) {
      setView("new");
      setRecordId(undefined);
      return;
    }
    const detailMatch = path.match(/\/(?:detalhe|editar)\/([^/]+)$/);
    if (detailMatch) {
      setView("detail");
      setRecordId(detailMatch[1]);
    }
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
