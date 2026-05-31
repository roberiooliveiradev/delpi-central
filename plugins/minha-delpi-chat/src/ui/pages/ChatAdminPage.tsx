import { useEffect, useState } from "react";

import { AdminAuditTab } from "../components/admin/audit/AdminAuditTab";
import { AdminAgentsTab } from "../components/admin/agents/AdminAgentsTab";
import { AdminSecurityTab } from "../components/admin/security/AdminSecurityTab";
import { AdminEvaluationsTab } from "../components/admin/evaluations/AdminEvaluationsTab";
import { AdminGuidelinesTab } from "../components/admin/guidelines/AdminGuidelinesTab";
import { AdminKnowledgeTab } from "../components/admin/knowledge/AdminKnowledgeTab";
import { AdminMetricsTab } from "../components/admin/metrics-tab/AdminMetricsTab";
import { AdminShellAlerts } from "../components/admin/shell/AdminShellAlerts";
import { AdminShellTopbar } from "../components/admin/shell/AdminShellTopbar";
import type { AdminTab, AdminTabItem } from "../components/admin/shell/adminShellTypes";
import { AdminSkillsTab } from "../components/admin/skills/AdminSkillsTab";
import { AdminSimulateTab } from "../components/admin/simulate/AdminSimulateTab";
import { AdminToolsTab } from "../components/admin/tools/AdminToolsTab";
import { AdminRbacPanel } from "../components/admin/rbac/AdminRbacPanel";
import { getAdminRbacSummary } from "../../data/api/adminApi";
import type { AdminRbacSummary } from "../../data/api/adminTypes";
import { testAdminRag } from "../../data/api/adminApi";
import { useChatAdmin } from "../../state/hooks/useChatAdmin";
import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  initialAgentId?: string | null;
  initialTab?: AdminTab;
  onBack: () => void;
};

const ADMIN_TABS: AdminTabItem[] = [
  { key: "knowledge", label: "Conhecimento" },
  { key: "metrics", label: "Métricas" },
  { key: "guidelines", label: "Diretrizes" },
  { key: "skills", label: "Habilidades" },
  { key: "simulate", label: "Simulação" },
  { key: "evaluations", label: "Avaliações" },
  { key: "agents", label: "Agentes" },
  { key: "security", label: "Segurança" },
  { key: "tools", label: "Ferramentas" },
  { key: "audit", label: "Auditoria" },
];

export function ChatAdminPage({
  getAccessToken,
  initialAgentId,
  initialTab,
  onBack,
}: ChatAdminPageProps) {
  const admin = useChatAdmin({ getAccessToken });
  const [activeTab, setActiveTab] = useState<AdminTab>(initialTab ?? "knowledge");
  const [adminRbac, setAdminRbac] = useState<AdminRbacSummary | null>(null);

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

  return (
    <main className="minha-delpi-chat mdc-admin-root mdc-chat-ws-directory">
      <AdminShellTopbar
        activeTab={activeTab}
        tabs={ADMIN_TABS}
        isLoading={admin.isLoading}
        onRefresh={admin.loadAdminData}
        onBack={onBack}
        onTabChange={setActiveTab}
      />

      <section className="mdc-admin-shell mdc-chat-ws-directory__main">
        <p className="mdc-chat-ws-directory__lead">
          Curadoria da base global, diretrizes, ferramentas e auditoria operacional.
        </p>

        <AdminShellAlerts
          error={admin.error}
          successMessage={admin.successMessage}
        />

        <ChatAnimatedPanel
          panelKey={activeTab}
          variant="tab"
          className="mdc-admin-shell__panel"
        >
        {activeTab === "knowledge" ? (
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


        {activeTab === "metrics" ? (
          <AdminMetricsTab
            metricsSummary={admin.metricsSummary}
            metricsHours={admin.metricsHours}
            onMetricsHoursChange={admin.setMetricsHours}
            getAccessToken={getAccessToken}
          />
        ) : null}

        {activeTab === "guidelines" ? (
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

        {activeTab === "skills" ? (
          <AdminSkillsTab getAccessToken={getAccessToken} rbac={adminRbac} />
        ) : null}

        {activeTab === "simulate" ? (
          <AdminSimulateTab getAccessToken={getAccessToken} />
        ) : null}

        {activeTab === "evaluations" ? (
          <AdminEvaluationsTab getAccessToken={getAccessToken} />
        ) : null}

        {activeTab === "agents" ? (
          <AdminAgentsTab
            getAccessToken={getAccessToken}
            initialAgentId={initialAgentId}
          />
        ) : null}

        {activeTab === "security" ? (
          <AdminSecurityTab getAccessToken={getAccessToken} />
        ) : null}

        {activeTab === "tools" ? (
          <div className="mdc-admin-tools-page">
            <AdminRbacPanel rbac={adminRbac} />
            <AdminToolsTab
              llmStatus={admin.llmStatus}
              getAccessToken={getAccessToken}
              rbac={adminRbac}
            />
          </div>
        ) : null}

        {activeTab === "audit" ? (
          <AdminAuditTab rbac={adminRbac} getAccessToken={getAccessToken} />
        ) : null}
        </ChatAnimatedPanel>
      </section>
    </main>
  );
}
