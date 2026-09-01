import { useCallback, useEffect, useMemo, useState } from "react";
import { AuditWorkspacePanel } from "../components/AuditWorkspacePanel";
import { AdminConfigImportExportPanel } from "../components/AdminConfigImportExportPanel";
import { AdminGoalsWorkspace } from "../components/AdminGoalsWorkspace";
import { CatalogAdminWorkspace } from "../components/CatalogAdminWorkspace";
import { InfoState } from "../components/InfoState";
import { LoadingActivityInline } from "../components/LoadingActivityInline";
import { RefreshSnapshotButton } from "../components/RefreshSnapshotButton";
import { SettingsOverviewWorkspace } from "../components/SettingsOverviewWorkspace";
import { SettingsStructuredEditor } from "../components/SettingsStructuredEditor";
import { SiPageHero, SiUnderlineNav } from "../components/siLayoutUi";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useCatalogStructureValidation } from "../../state/hooks/useCatalogStructureValidation";
import { useStrategicIndicatorsSettings } from "../../state/hooks/useStrategicIndicatorsSettings";
import { SI_HELP } from "../../content/helpTooltips";
import {
  readSettingsAdminRoute,
  writeSettingsAdminRoute,
  type CatalogAdminView,
  type SettingsAdminTab,
} from "../settings/settingsAdminTabs";
import "./SettingsPage.css";

type SettingsPageProps = {
  getAccessToken?: () => string | undefined;
};

const SETTINGS_LAYOUT_CLASS = "si-settings-active";

function formatSyncLine(updatedAt: string | null, updatedByEmail: string | null): string {
  if (!updatedAt) return "Sem registro de sincronização administrativa.";
  const when = new Date(updatedAt).toLocaleString("pt-BR");
  return updatedByEmail
    ? `Sync ${when} · por ${updatedByEmail}`
    : `Sync ${when}`;
}

export function SettingsPage({ getAccessToken }: SettingsPageProps) {
  const settings = useStrategicIndicatorsSettings({ getAccessToken });
  const validation = useCatalogStructureValidation({ getAccessToken });

  const initialRoute = useMemo(() => readSettingsAdminRoute(), []);
  const [activeTab, setActiveTab] = useState<SettingsAdminTab>(initialRoute.tab);
  const [catalogView, setCatalogView] = useState<CatalogAdminView>(
    initialRoute.catalogView,
  );

  useEffect(() => {
    document.documentElement.classList.add(SETTINGS_LAYOUT_CLASS);
    return () => {
      document.documentElement.classList.remove(SETTINGS_LAYOUT_CLASS);
    };
  }, []);

  useEffect(() => {
    writeSettingsAdminRoute(activeTab, catalogView);
  }, [activeTab, catalogView]);

  useEffect(() => {
    const onPopState = () => {
      const route = readSettingsAdminRoute();
      setActiveTab(route.tab);
      setCatalogView(route.catalogView);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = useCallback(
    (tab: SettingsAdminTab, nextCatalogView: CatalogAdminView = "structure") => {
      setActiveTab(tab);
      if (tab === "catalog") {
        setCatalogView(nextCatalogView);
      }
    },
    [],
  );

  const globalLoadingProgress = useLoadingProgress(
    settings.loading && activeTab === "system",
    settings.requestProgress,
  );

  const validationIssueCount =
    validation.summary.errors +
    validation.summary.warnings +
    validation.summary.infos;

  const syncDescription = formatSyncLine(
    settings.data?.meta.updated_at ?? null,
    settings.data?.meta.updated_by_email ?? null,
  );

  const navItems = useMemo(
    () => [
      {
        id: "overview",
        label: "Início",
        title: SI_HELP.nav.overview,
        onSelect: () => navigate("overview"),
      },
      {
        id: "catalog",
        label: "Catálogo",
        title: SI_HELP.nav.catalog,
        count: validationIssueCount > 0 ? validationIssueCount : undefined,
        onSelect: () => navigate("catalog", "structure"),
      },
      {
        id: "goals",
        label: "Metas",
        title: SI_HELP.nav.goals,
        onSelect: () => navigate("goals"),
      },
      {
        id: "system",
        label: "Sistema",
        title: SI_HELP.nav.system,
        onSelect: () => navigate("system"),
      },
    ],
    [navigate, validationIssueCount],
  );

  return (
    <div className="si-settings-page">
      <SiPageHero
        density="compact"
        eyebrow="Indicadores Estratégicos"
        title="Administração"
        description={syncDescription}
        actions={
          <RefreshSnapshotButton
            getAccessToken={getAccessToken}
            onRefreshed={() => {
              void settings.reload();
              void validation.reload();
            }}
            disabled={settings.loading || settings.saving}
          />
        }
      />

      {settings.loading ? (
        <div className="si-settings-page__status si-settings-page__status--neutral">
          Carregando configurações…
        </div>
      ) : null}

      {settings.error ? (
        <div className="si-settings-page__status si-settings-page__status--error">
          <span>{settings.error}</span>
          <button type="button" onClick={() => void settings.reload()}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {settings.successMessage ? (
        <div className="si-settings-page__status si-settings-page__status--success">
          <span>{settings.successMessage}</span>
          <button type="button" onClick={settings.clearSuccessMessage}>
            Fechar
          </button>
        </div>
      ) : null}

      <div className="si-settings-shell">
        <aside className="si-settings-shell__nav">
          <SiUnderlineNav
            className="si-settings-admin-nav"
            aria-label="Administração SI"
            activeId={activeTab}
            mode="navigation"
            layout="wrap"
            items={navItems}
          />
        </aside>

        <div className="si-settings-shell__main">
          {activeTab === "overview" ? (
            <SettingsOverviewWorkspace
              validation={validation}
              onNavigate={navigate}
            />
          ) : null}

          {activeTab === "catalog" ? (
            <CatalogAdminWorkspace
              getAccessToken={getAccessToken}
              view={catalogView}
              validationIssueCount={validationIssueCount}
              onViewChange={setCatalogView}
            />
          ) : null}

          {activeTab === "goals" ? (
            <AdminGoalsWorkspace getAccessToken={getAccessToken} />
          ) : null}

          {activeTab === "system" ? (
            <div className="si-settings-system">
              {settings.loading && !settings.data ? (
                <LoadingActivityInline
                  title="Carregando sistema"
                  description="Parâmetros, governança e auditoria."
                  variant="panel"
                  tone="info"
                  progressPercent={globalLoadingProgress}
                />
              ) : !settings.data ? (
                <InfoState
                  title="Sistema indisponível"
                  description="Não foi possível carregar parâmetros e governança."
                />
              ) : (
                <>
                  <SettingsStructuredEditor
                    data={settings.data}
                    saving={settings.saving}
                    onSave={settings.save}
                  />
                  <AdminConfigImportExportPanel
                    getAccessToken={getAccessToken}
                    onCompleted={() => {
                      void settings.reload();
                      void validation.reload();
                    }}
                  />
                  <AuditWorkspacePanel getAccessToken={getAccessToken} />
                </>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
