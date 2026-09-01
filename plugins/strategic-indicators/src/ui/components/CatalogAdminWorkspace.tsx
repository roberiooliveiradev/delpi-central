import { useEffect, useState } from "react";
import { AdminDepartmentsWorkspace } from "./AdminDepartmentsWorkspace";
import { CatalogStructureValidationWorkspace } from "./CatalogStructureValidationWorkspace";
import { SiUnderlineNav } from "./siLayoutUi";
import type { CatalogAdminView } from "../settings/settingsAdminTabs";
import "./CatalogAdminWorkspace.css";

type CatalogAdminWorkspaceProps = {
  getAccessToken?: () => string | undefined;
  view: CatalogAdminView;
  validationIssueCount?: number;
  onViewChange: (view: CatalogAdminView) => void;
};

export function CatalogAdminWorkspace({
  getAccessToken,
  view,
  validationIssueCount = 0,
  onViewChange,
}: CatalogAdminWorkspaceProps) {
  const [activeView, setActiveView] = useState<CatalogAdminView>(view);

  useEffect(() => {
    setActiveView(view);
  }, [view]);

  function selectView(nextView: CatalogAdminView) {
    setActiveView(nextView);
    onViewChange(nextView);
  }

  const issueBadge =
    validationIssueCount > 0 ? validationIssueCount : undefined;

  return (
    <div className="si-catalog-admin">
      <SiUnderlineNav
        className="si-catalog-admin__subnav"
        aria-label="Catálogo"
        activeId={activeView}
        mode="tabs"
        density="compact"
        items={[
          {
            id: "structure",
            label: "Estrutura",
            onSelect: () => selectView("structure"),
          },
          {
            id: "validation",
            label: "Validação",
            count: issueBadge,
            onSelect: () => selectView("validation"),
          },
        ]}
      />

      <div className="si-catalog-admin__panel">
        {activeView === "structure" ? (
          <AdminDepartmentsWorkspace getAccessToken={getAccessToken} />
        ) : (
          <CatalogStructureValidationWorkspace getAccessToken={getAccessToken} />
        )}
      </div>
    </div>
  );
}
