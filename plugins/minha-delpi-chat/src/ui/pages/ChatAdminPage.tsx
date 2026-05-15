import { useState } from "react";

import { AdminAuditTab } from "../components/admin/AdminAuditTab";
import { AdminGuidelinesTab } from "../components/admin/AdminGuidelinesTab";
import { AdminKnowledgeTab } from "../components/admin/AdminKnowledgeTab";
import { AdminMetrics } from "../components/admin/AdminMetrics";
import { AdminToolsTab } from "../components/admin/AdminToolsTab";
import { useChatAdmin } from "../../state/hooks/useChatAdmin";

import "./ChatAdminPage.css";

type ChatAdminPageProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onBack: () => void;
};

type AdminTab = "knowledge" | "guidelines" | "tools" | "audit";

const ADMIN_TABS: Array<{ key: AdminTab; label: string }> = [
  { key: "knowledge", label: "Conhecimento" },
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
        <header className="mdc-admin-topbar">
          <div className="mdc-admin-topbar__content">
            <div>
              <p className="mdc-chat-eyebrow">Administração</p>
              <h1>Minha DELPI Chat</h1>
              <p>
                Curadoria da base global, diretrizes, ferramentas e auditoria operacional.
              </p>
            </div>

            <div className="mdc-admin-actions">
              <button type="button" onClick={admin.loadAdminData} disabled={admin.isLoading}>
                Atualizar
              </button>
              <button type="button" onClick={onBack}>
                Voltar ao chat
              </button>
            </div>
          </div>

          <nav className="mdc-admin-tabs" aria-label="Administração do chat">
            {ADMIN_TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                className={activeTab === tab.key ? "is-active" : undefined}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </header>

        {admin.error ? (
          <div className="mdc-chat-alert" role="alert">
            {admin.error}
          </div>
        ) : null}

        {admin.successMessage ? (
          <div className="mdc-chat-alert mdc-chat-alert--success" role="status">
            {admin.successMessage}
          </div>
        ) : null}

        <AdminMetrics metricsSummary={admin.metricsSummary} />

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

        {activeTab === "guidelines" ? <AdminGuidelinesTab /> : null}

        {activeTab === "tools" ? <AdminToolsTab llmStatus={admin.llmStatus} /> : null}

        {activeTab === "audit" ? <AdminAuditTab auditLogs={admin.auditLogs} /> : null}
      </section>
    </main>
  );
}
