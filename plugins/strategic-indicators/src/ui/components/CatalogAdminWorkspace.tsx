import { useCallback, useEffect, useState } from "react";
import { AdminDepartmentsWorkspace } from "./AdminDepartmentsWorkspace";
import { CatalogStructureValidationWorkspace } from "./CatalogStructureValidationWorkspace";
import { SiUnderlineNav } from "./siLayoutUi";
import type {
  CatalogAdminAction,
  CatalogAdminView,
  GoalsAdminAction,
  SettingsAdminTab,
} from "../settings/settingsAdminTabs";
import "./CatalogAdminWorkspace.css";

type CatalogAdminWorkspaceProps = {
  getAccessToken?: () => string | undefined;
  view: CatalogAdminView;
  validationIssueCount?: number;
  catalogAction?: CatalogAdminAction | null;
  onViewChange: (view: CatalogAdminView) => void;
  onNavigate?: (
    tab: SettingsAdminTab,
    catalogView?: CatalogAdminView,
    options?: {
      catalogAction?: CatalogAdminAction | null;
      goalsAction?: GoalsAdminAction | null;
    },
  ) => void;
  onCatalogActionConsumed?: () => void;
};

export function CatalogAdminWorkspace({
  getAccessToken,
  view,
  validationIssueCount = 0,
  catalogAction = null,
  onViewChange,
  onNavigate,
  onCatalogActionConsumed,
}: CatalogAdminWorkspaceProps) {
  const [activeView, setActiveView] = useState<CatalogAdminView>(view);
  const [structureFocus, setStructureFocus] = useState<{
    departmentId: string;
    indicatorId: string;
  } | null>(null);

  const clearStructureFocus = useCallback(() => setStructureFocus(null), []);

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
          <AdminDepartmentsWorkspace
            getAccessToken={getAccessToken}
            structureFocus={structureFocus}
            catalogAction={catalogAction}
            onStructureFocusConsumed={clearStructureFocus}
            onCatalogActionConsumed={onCatalogActionConsumed}
          />
        ) : (
          <CatalogStructureValidationWorkspace
            getAccessToken={getAccessToken}
            onOpenIndicator={(departmentId, indicatorId) => {
              setStructureFocus({ departmentId, indicatorId });
              selectView("structure");
            }}
            onOpenGoals={() => onNavigate?.("goals")}
          />
        )}
      </div>
    </div>
  );
}
