import { useEffect, useMemo, useState } from "react";

import { listPath, newPath, parseRoute } from "../constants/kaizen";
import { KaizenFormPage } from "./KaizenFormPage";
import { KaizenListPage } from "./KaizenListPage";

type View = "list" | "new" | "edit";

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
    const editMatch = path.match(/\/editar\/([^/]+)$/);
    if (editMatch) {
      setView("edit");
      setRecordId(editMatch[1]);
    }
  }

  if (view === "new") {
    return <KaizenFormPage mode="new" onNavigate={handleNavigate} />;
  }

  if (view === "edit" && recordId) {
    return <KaizenFormPage mode="edit" recordId={recordId} onNavigate={handleNavigate} />;
  }

  return <KaizenListPage onNavigate={handleNavigate} />;
}
