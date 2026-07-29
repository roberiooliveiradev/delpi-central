import { useEffect, useMemo, useState } from "react";

import { detailPath, parseRoute, type View } from "../constants/kaizen";
import { navigateKaizen } from "../utils/navigation";
import {
  branchOptionsForPermissions,
  defaultBranchCode,
} from "../utils/kaizenBranchPermissions";
import { KaizenDashboardPage } from "./KaizenDashboardPage";
import { KaizenDetailPage } from "./KaizenDetailPage";
import { KaizenFormPage } from "./KaizenFormPage";
import { KaizenListPage } from "./KaizenListPage";

type Props = {
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export function CadastroKaizenPage({ pathname, permissions, isSuperadmin }: Props) {
  const externalRoute = useMemo(() => parseRoute(pathname), [pathname]);
  const [view, setView] = useState<View>(externalRoute.view);
  const [recordId, setRecordId] = useState<string | undefined>(externalRoute.id);

  const branchOptions = useMemo(
    () => branchOptionsForPermissions(permissions, isSuperadmin),
    [permissions, isSuperadmin],
  );
  const defaultBranch = useMemo(
    () => defaultBranchCode(permissions, isSuperadmin),
    [permissions, isSuperadmin],
  );

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
    return (
      <KaizenDashboardPage
        onNavigate={handleNavigate}
        branchOptions={branchOptions}
      />
    );
  }

  if (view === "new") {
    return (
      <KaizenFormPage
        mode="new"
        onNavigate={handleNavigate}
        onCreated={(id) => handleNavigate(detailPath(id))}
        branchOptions={branchOptions}
        defaultBranchCode={defaultBranch}
      />
    );
  }

  if ((view === "detail" || view === "edit") && recordId) {
    return (
      <KaizenDetailPage
        recordId={recordId}
        onNavigate={handleNavigate}
        branchOptions={branchOptions}
      />
    );
  }

  return (
    <KaizenListPage
      onNavigate={handleNavigate}
      branchOptions={branchOptions}
    />
  );
}
