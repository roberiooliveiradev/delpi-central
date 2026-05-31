import { useCallback, useEffect, useState } from "react";

import {
  buildAdminHref,
  legacyTabToNav,
  normalizeAdminNav,
  adminNavPanelKey,
  type AdminNavState,
  type LegacyAdminTab,
} from "../../navigation/adminNavigation";
import { navigateChatHref } from "../../navigation/chatNavigation";
import { AdminAuditTab } from "../components/admin/audit/AdminAuditTab";
import { AdminAgentsTab } from "../components/admin/agents/AdminAgentsTab";
import { AdminSecurityTab } from "../components/admin/security/AdminSecurityTab";
import { AdminEvaluationsTab } from "../components/admin/evaluations/AdminEvaluationsTab";
import { AdminGuidelinesTab } from "../components/admin/guidelines/AdminGuidelinesTab";
import { AdminKnowledgeTab } from "../components/admin/knowledge/AdminKnowledgeTab";
import { AdminMetricsTab } from "../components/admin/metrics-tab/AdminMetricsTab";
import { AdminOverviewTab } from "../components/admin/overview/AdminOverviewTab";
import { AdminPlatformIntelligenceTab } from "../components/admin/platform/AdminPlatformIntelligenceTab";
import { AdminShellAlerts } from "../components/admin/shell/AdminShellAlerts";
import { AdminShellTopbar } from "../components/admin/shell/AdminShellTopbar";
import { AdminSkillsTab } from "../components/admin/skills/AdminSkillsTab";
import { AdminSimulateTab } from "../components/admin/simulate/AdminSimulateTab";
import { AdminToolsTab } from "../components/admin/tools/AdminToolsTab";
import { getAdminRbacSummary } from "../../data/api/adminApi";
import type { AdminRbacSummary } from "../../data/api/adminTypes";
import { testAdminRag } from "../../data/api/adminApi";
import { useChatAdmin } from "../../state/hooks/useChatAdmin";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  initialNav?: Partial<AdminNavState>;
  /** @deprecated Use initialNav */
  initialAgentId?: string | null;
  /** @deprecated Use initialNav */
  initialTab?: LegacyAdminTab;
  onBack: () => void;
};

function resolveInitialNav(
  initialNav?: Partial<AdminNavState>,
  initialTab?: LegacyAdminTab,
  initialAgentId?: string | null,
): AdminNavState {
  if (initialNav) {
    return normalizeAdminNav({ ...initialNav, agentId: initialNav.agentId ?? initialAgentId });
  }

  if (initialTab) {
    return legacyTabToNav(initialTab, initialAgentId);
  }

  return normalizeAdminNav({ agentId: initialAgentId });
}

export function ChatAdminPage({
  getAccessToken,
  initialNav,
  initialAgentId,
  initialTab,
  onBack,
}: ChatAdminPageProps) {
  const admin = useChatAdmin({ getAccessToken });
  const [nav, setNav] = useState<AdminNavState>(() =>
    resolveInitialNav(initialNav, initialTab, initialAgentId),
  );
  const [adminRbac, setAdminRbac] = useState<AdminRbacSummary | null>(null);

  const applyNav = useCallback((partial: Partial<AdminNavState>) => {
    setNav((current) => {
      const next = normalizeAdminNav({ ...current, ...partial });
      navigateChatHref(buildAdminHref(next));

      return next;
    });
  }, []);

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

  function renderPanel() {
    if (nav.section === "overview") {
      return (
        <AdminOverviewTab
          metricsSummary={admin.metricsSummary}
          llmStatus={admin.llmStatus}
          rbac={adminRbac}
          isLoading={admin.isLoading}
          getAccessToken={getAccessToken}
          onNavigate={applyNav}
        />
      );
    }

    if (nav.section === "knowledge" && nav.subTab === "documents") {
      return (
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
            testAdminRag({ question: "Resuma este documento.", documentId }, { getAccessToken }).then(
              () => undefined,
            )
          }
          rbac={adminRbac}
        />
      );
    }

    if (nav.section === "knowledge" && nav.subTab === "guidelines") {
      return (
        <AdminGuidelinesTab
          guidelines={admin.guidelines}
          saveGuideline={admin.saveGuideline}
          publishGuideline={admin.publishGuideline}
          archiveGuideline={admin.archiveGuideline}
          reloadAdminData={admin.loadAdminData}
          getAccessToken={getAccessToken}
          rbac={adminRbac}
          testGuidelines={(question) => testAdminRag({ question }, { getAccessToken })}
        />
      );
    }

    if (nav.section === "knowledge" && nav.subTab === "behaviors") {
      return <AdminSkillsTab getAccessToken={getAccessToken} rbac={adminRbac} />;
    }

    if (nav.section === "agents" && nav.subTab === "simulation") {
      return <AdminSimulateTab getAccessToken={getAccessToken} />;
    }

    if (nav.section === "agents" && nav.subTab === "specialization") {
      return (
        <AdminAgentsTab getAccessToken={getAccessToken} initialAgentId={nav.agentId ?? initialAgentId} />
      );
    }

    if (nav.section === "quality" && nav.subTab === "metrics") {
      return (
        <AdminMetricsTab
          metricsSummary={admin.metricsSummary}
          metricsHours={admin.metricsHours}
          onMetricsHoursChange={admin.setMetricsHours}
          getAccessToken={getAccessToken}
        />
      );
    }

    if (nav.section === "quality" && nav.subTab === "evaluations") {
      return <AdminEvaluationsTab getAccessToken={getAccessToken} />;
    }

    if (nav.section === "platform" && nav.subTab === "tools") {
      return (
        <AdminToolsTab
          llmStatus={admin.llmStatus}
          getAccessToken={getAccessToken}
          rbac={adminRbac}
        />
      );
    }

    if (nav.section === "platform" && nav.subTab === "intelligence") {
      return <AdminPlatformIntelligenceTab getAccessToken={getAccessToken} />;
    }

    if (nav.section === "governance" && nav.subTab === "security") {
      return <AdminSecurityTab getAccessToken={getAccessToken} />;
    }

    if (nav.section === "governance" && nav.subTab === "audit") {
      return <AdminAuditTab rbac={adminRbac} getAccessToken={getAccessToken} />;
    }

    return null;
  }

  return (
    <main className="minha-delpi-chat mdc-admin-root">
      <section className="mdc-admin-shell">
        <AdminShellTopbar
          nav={nav}
          isLoading={admin.isLoading}
          onRefresh={admin.loadAdminData}
          onBack={onBack}
          onNavChange={applyNav}
        />

        <AdminShellAlerts error={admin.error} successMessage={admin.successMessage} />

        <ChatAnimatedPanel
          panelKey={adminNavPanelKey(nav)}
          variant="tab"
          className="mdc-admin-shell__panel"
        >
          {renderPanel()}
        </ChatAnimatedPanel>
      </section>
    </main>
  );
}
