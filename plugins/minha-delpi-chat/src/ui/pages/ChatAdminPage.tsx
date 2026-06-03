import { useCallback, useEffect, useMemo, useState } from "react";

import { AdminAuditTab } from "../components/admin/audit/AdminAuditTab";
import { AdminAgentsTab } from "../components/admin/agents/AdminAgentsTab";
import { AdminSecurityTab } from "../components/admin/security/AdminSecurityTab";
import { AdminEvaluationsTab } from "../components/admin/evaluations/AdminEvaluationsTab";
import { AdminGuidelinesTab } from "../components/admin/guidelines/AdminGuidelinesTab";
import { AdminKnowledgeTab } from "../components/admin/knowledge/AdminKnowledgeTab";
import { AdminMetricsTab } from "../components/admin/metrics-tab/AdminMetricsTab";
import { AdminOverviewTab } from "../components/admin/overview/AdminOverviewTab";
import { AdminShellAlerts } from "../components/admin/shell/AdminShellAlerts";
import { AdminShellStatusStrip } from "../components/admin/shell/AdminShellStatusStrip";
import { AdminShellTopbar } from "../components/admin/shell/AdminShellTopbar";
import { AdminSubTabNav } from "../components/admin/shell/AdminSubTabNav";
import type { AdminLegacyTab, AdminNavState } from "../../navigation/adminNavigation";
import { AdminSkillsTab } from "../components/admin/skills/AdminSkillsTab";
import { AdminSimulateTab } from "../components/admin/simulate/AdminSimulateTab";
import { AdminToolsTab } from "../components/admin/tools/AdminToolsTab";
import { getAdminRbacSummary } from "../../data/api/adminApi";
import type { AdminRbacSummary } from "../../data/api/adminTypes";
import { testAdminRag } from "../../data/api/adminApi";
import {
  buildAdminHref,
  defaultSubTabForSection,
  getAdminSectionItem,
  legacyTabToNav,
  normalizeAdminNav,
  warnLegacyAdminTab,
} from "../../navigation/adminNavigation";
import { navigateChatHref } from "../../navigation/chatNavigation";
import { useChatAdmin } from "../../state/hooks/useChatAdmin";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  initialAgentId?: string | null;
  /** @deprecated Preferir initialNav */
  initialTab?: AdminLegacyTab;
  initialNav?: AdminNavState;
  onBack: () => void;
};

function resolveInitialNav(
  initialNav?: AdminNavState,
  initialTab?: AdminLegacyTab,
  initialAgentId?: string | null,
): AdminNavState {
  if (initialNav) {
    return normalizeAdminNav(initialNav);
  }

  if (initialTab) {
    warnLegacyAdminTab(initialTab);
    return legacyTabToNav(initialTab);
  }

  if (initialAgentId) {
    return { section: "agents", subTab: "specialization" };
  }

  return { section: "overview" };
}

export function ChatAdminPage({
  getAccessToken,
  initialAgentId,
  initialTab,
  initialNav,
  onBack,
}: ChatAdminPageProps) {
  const admin = useChatAdmin({ getAccessToken });
  const [nav, setNav] = useState<AdminNavState>(() =>
    resolveInitialNav(initialNav, initialTab, initialAgentId),
  );
  const [adminRbac, setAdminRbac] = useState<AdminRbacSummary | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  const sectionMeta = useMemo(() => getAdminSectionItem(nav.section), [nav.section]);

  useEffect(() => {
    setNav(resolveInitialNav(initialNav, initialTab, initialAgentId));
  }, [initialNav, initialTab, initialAgentId]);

  useEffect(() => {
    async function loadAdminRbac() {
      try {
        const summary = await getAdminRbacSummary({ getAccessToken });
        setAdminRbac(summary);
      } catch {
        setAdminRbac(null);
      }
    }

    void loadAdminRbac();
  }, [getAccessToken]);

  const navigateTo = useCallback((next: AdminNavState) => {
    const normalized = normalizeAdminNav(next);
    setNav(normalized);
    navigateChatHref(buildAdminHref(normalized));
  }, []);

  const handleSectionChange = useCallback(
    (section: AdminNavState["section"]) => {
      navigateTo({
        section,
        subTab: defaultSubTabForSection(section),
      });
    },
    [navigateTo],
  );

  const handleSubTabChange = useCallback(
    (subTab: NonNullable<AdminNavState["subTab"]>) => {
      if (nav.section === "overview") {
        return;
      }

      navigateTo({ section: nav.section, subTab });
    },
    [nav.section, navigateTo],
  );

  const handleRefresh = useCallback(() => {
    void admin.loadAdminData().then(() => {
      setLastUpdatedAt(new Date());
    });
  }, [admin]);

  const openAuditFromSecurity = useCallback(() => {
    navigateTo({ section: "governance", subTab: "audit" });
  }, [navigateTo]);

  const panelKey = `${nav.section}:${nav.subTab ?? "root"}`;

  return (
    <main className="minha-delpi-chat mdc-admin-root mdc-chat-ws-directory">
      <AdminShellTopbar
        nav={nav}
        isLoading={admin.isLoading}
        onRefresh={handleRefresh}
        onBack={onBack}
        onSectionChange={handleSectionChange}
      />

      <section className="mdc-admin-shell mdc-chat-ws-directory__main">
        <p className="mdc-chat-ws-directory__lead">{sectionMeta.description}</p>

        <AdminShellStatusStrip
          error={admin.error}
          successMessage={admin.successMessage}
          lastUpdatedAt={lastUpdatedAt}
          isLoading={admin.isLoading}
          onRefresh={handleRefresh}
        />

        <AdminSubTabNav nav={nav} onSubTabChange={handleSubTabChange} />

        <AdminShellAlerts
          error={admin.error}
          successMessage={admin.successMessage}
        />

        <ChatAnimatedPanel
          panelKey={panelKey}
          variant="tab"
          className="mdc-admin-shell__panel"
        >
          {nav.section === "overview" ? (
            <AdminOverviewTab
              metricsSummary={admin.metricsSummary}
              getAccessToken={getAccessToken}
              onNavigate={navigateTo}
            />
          ) : null}

          {nav.section === "knowledge" && nav.subTab === "documents" ? (
            <AdminKnowledgeTab
              documents={admin.documents}
              documentsPagination={admin.documentsPagination}
              documentSearch={admin.documentSearch}
              documentStatus={admin.documentStatus}
              documentCategory={admin.documentCategory}
              documentNamespace={admin.documentNamespace}
              documentDomain={admin.documentDomain}
              documentTag={admin.documentTag}
              documentSourceType={admin.documentSourceType}
              documentFacets={admin.documentFacets}
              documentSummary={admin.documentSummary}
              onDocumentStatusFilterChange={admin.setDocumentStatus}
              isLoading={admin.isLoading}
              isMutating={admin.isMutating}
              setDocumentSearch={admin.setDocumentSearch}
              setDocumentStatus={admin.setDocumentStatus}
              setDocumentCategory={admin.setDocumentCategory}
              setDocumentNamespace={admin.setDocumentNamespace}
              setDocumentDomain={admin.setDocumentDomain}
              setDocumentTag={admin.setDocumentTag}
              setDocumentSourceType={admin.setDocumentSourceType}
              resetDocumentCuratorialFilters={admin.resetDocumentCuratorialFilters}
              goToNextDocumentsPage={admin.goToNextDocumentsPage}
              goToPreviousDocumentsPage={admin.goToPreviousDocumentsPage}
              createDocument={admin.createDocument}
              uploadDocumentFile={admin.uploadDocumentFile}
              previewIngestion={admin.previewIngestion}
              ingestionPreview={admin.ingestionPreview}
              deleteDocument={admin.deleteDocument}
              deactivateDocument={admin.deactivateDocument}
              reactivateDocument={admin.reactivateDocument}
              reindexDocument={admin.reindexDocument}
              updateDocumentMetadata={admin.updateDocumentMetadata}
              testDocument={(documentId) =>
                testAdminRag({ question: "Resuma este documento.", documentId }, { getAccessToken })
                  .then(() => undefined)
              }
              rbac={adminRbac}
            />
          ) : null}

          {nav.section === "knowledge" && nav.subTab === "guidelines" ? (
            <AdminGuidelinesTab
              guidelines={admin.guidelines}
              saveGuideline={admin.saveGuideline}
              publishGuideline={admin.publishGuideline}
              archiveGuideline={admin.archiveGuideline}
              reloadAdminData={admin.loadAdminData}
              getAccessToken={getAccessToken}
              rbac={adminRbac}
              testGuidelines={(question) =>
                testAdminRag({ question }, { getAccessToken })
              }
            />
          ) : null}

          {nav.section === "knowledge" && nav.subTab === "behaviors" ? (
            <AdminSkillsTab getAccessToken={getAccessToken} rbac={adminRbac} />
          ) : null}

          {nav.section === "agents" && nav.subTab === "specialization" ? (
            <AdminAgentsTab
              getAccessToken={getAccessToken}
              initialAgentId={initialAgentId}
            />
          ) : null}

          {nav.section === "agents" && nav.subTab === "simulation" ? (
            <AdminSimulateTab getAccessToken={getAccessToken} />
          ) : null}

          {nav.section === "quality" && nav.subTab === "metrics" ? (
            <AdminMetricsTab
              metricsSummary={admin.metricsSummary}
              metricsHours={admin.metricsHours}
              onMetricsHoursChange={admin.setMetricsHours}
              onRefresh={() => void admin.loadAdminData()}
              isRefreshing={admin.isLoading}
              getAccessToken={getAccessToken}
              onNavigate={navigateTo}
            />
          ) : null}

          {nav.section === "quality" && nav.subTab === "evaluations" ? (
            <AdminEvaluationsTab getAccessToken={getAccessToken} />
          ) : null}

          {nav.section === "platform" && nav.subTab === "tools" ? (
            <AdminToolsTab
              llmStatus={admin.llmStatus}
              getAccessToken={getAccessToken}
              rbac={adminRbac}
              view="tools"
            />
          ) : null}

          {nav.section === "platform" && nav.subTab === "intelligence" ? (
            <AdminToolsTab
              getAccessToken={getAccessToken}
              rbac={adminRbac}
              view="intelligence"
            />
          ) : null}

          {nav.section === "governance" && nav.subTab === "security" ? (
            <AdminSecurityTab
              getAccessToken={getAccessToken}
              rbac={adminRbac}
              onOpenAudit={openAuditFromSecurity}
            />
          ) : null}

          {nav.section === "governance" && nav.subTab === "audit" ? (
            <AdminAuditTab rbac={adminRbac} getAccessToken={getAccessToken} />
          ) : null}
        </ChatAnimatedPanel>
      </section>
      <div id="mdc-modal-root" className="mdc-modal-root" aria-hidden="true" />
    </main>
  );
}
