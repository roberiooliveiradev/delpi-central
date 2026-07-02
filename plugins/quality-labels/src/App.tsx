import { useState } from "react";
import { ClipboardList, History, UserCheck } from "lucide-react";

import { configureHttpClient } from "./api/httpClient";
import { QualityLabelsAdminPage } from "./pages/QualityLabelsAdminPage";
import { QualityLabelsAuditPage } from "./pages/QualityLabelsAuditPage";
import { QualityLabelsInspectorPage } from "./pages/QualityLabelsInspectorPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

type TabId = "labels" | "inspector" | "audit";

export default function App({ getAccessToken }: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const [tab, setTab] = useState<TabId>("labels");

  return (
    <div className="quality-labels">
      <div className="quality-labels-page">
        <div className="ql-inner">
          <header className="ql-hero">
            <p className="ql-eyebrow">Qualidade</p>
            <span className="ql-eyebrow-mark" />
            <h1 className="ql-title">Etiquetas da Qualidade</h1>
            <p className="ql-subtitle">
              Registre inspeções por ordem de produção, gere a etiqueta com QR code e
              acompanhe toda a trilha de auditoria da aplicação.
            </p>
          </header>

          <nav className="ql-tabs" role="tablist" aria-label="Seções">
            <button
              type="button"
              role="tab"
              aria-selected={tab === "labels"}
              className={`ql-tab ${tab === "labels" ? "ql-tab--active" : ""}`}
              onClick={() => setTab("labels")}
            >
              <ClipboardList className="ql-icon" />
              Etiquetas
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "inspector"}
              className={`ql-tab ${tab === "inspector" ? "ql-tab--active" : ""}`}
              onClick={() => setTab("inspector")}
            >
              <UserCheck className="ql-icon" />
              Inspetor
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "audit"}
              className={`ql-tab ${tab === "audit" ? "ql-tab--active" : ""}`}
              onClick={() => setTab("audit")}
            >
              <History className="ql-icon" />
              Auditoria
            </button>
          </nav>

          {tab === "labels" && <QualityLabelsAdminPage />}
          {tab === "inspector" && <QualityLabelsInspectorPage />}
          {tab === "audit" && <QualityLabelsAuditPage />}
        </div>
      </div>
    </div>
  );
}
