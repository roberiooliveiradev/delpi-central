import { useState } from "react";

import { AdminAuditTab } from "../components/admin/audit/AdminAuditTab";
import { AdminGuidelinesTab } from "../components/admin/guidelines/AdminGuidelinesTab";
import { AdminKnowledgeTab } from "../components/admin/knowledge/AdminKnowledgeTab";
import { AdminMetricsTab } from "../components/admin/metrics-tab/AdminMetricsTab";
import { AdminShellAlerts } from "../components/admin/shell/AdminShellAlerts";
import { AdminShellTopbar } from "../components/admin/shell/AdminShellTopbar";
import type { AdminTab, AdminTabItem } from "../components/admin/shell/adminShellTypes";
import { AdminToolsTab } from "../components/admin/tools/AdminToolsTab";
import { testAdminRag } from "../../data/api/adminFutureApi";
import { useChatAdmin } from "../../state/hooks/useChatAdmin";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onBack: () => void;
};

const ADMIN_TABS: AdminTabItem[] = [
  { key: "knowledge", label: "Conhecimento" },
  { key: "metrics", label: "Métricas" },
  { key: "guidelines", label: "Diretrizes" },
  { key: "tools", label: "Ferramentas" },
  { key: "audit", label: "Auditoria" },
];

export function ChatAdminPage({ getAccessToken, onBack }: ChatAdminPageProps) {
  const admin = useChatAdmin({ getAccessToken });
  const [activeTab, setActiveTab] = useState<AdminTab>("knowledge");

  return (
    <main className="minha-delpi-chat mdc-admin-root">
      <section className="mdc-admin-shell">
        <AdminShellTopbar
          activeTab={activeTab}
          tabs={ADMIN_TABS}
          isLoading={admin.isLoading}
          onRefresh={admin.loadAdminData}
          onBack={onBack}
          onTabChange={setActiveTab}
        />

        <AdminShellAlerts
          error={admin.error}
          successMessage={admin.successMessage}
        />

        {activeTab === "knowledge" ? (
          <AdminKnowledgeTab
            documents={admin.documents}
            documentsPagination={admin.documentsPagination}
            documentSearch={admin.documentSearch}
            documentStatus={admin.documentStatus}
            isLoading={admin.isLoading}
            isMutating={admin.isMutating}
            setDocumentSearch={admin.setDocumentSearch}
            setDocumentStatus={admin.setDocumentStatus}
            goToNextDocumentsPage={admin.goToNextDocumentsPage}
            goToPreviousDocumentsPage={admin.goToPreviousDocumentsPage}
            createDocument={admin.createDocument}
            uploadDocumentFile={admin.uploadDocumentFile}
            deleteDocument={admin.deleteDocument}
            deactivateDocument={admin.deactivateDocument}
            reactivateDocument={admin.reactivateDocument}
            reindexDocument={admin.reindexDocument}
          />
        ) : null}


        {activeTab === "metrics" ? (
          <AdminMetricsTab metricsSummary={admin.metricsSummary} />
        ) : null}

        {activeTab === "guidelines" ? (
          <AdminGuidelinesTab
            testGuidelines={(question) =>
              testAdminRag({ question }, { getAccessToken })
            }
          />
        ) : null}

        {activeTab === "tools" ? <AdminToolsTab llmStatus={admin.llmStatus} /> : null}

        {activeTab === "audit" ? <AdminAuditTab auditLogs={admin.auditLogs} /> : null}
      </section>
    </main>
  );
}
