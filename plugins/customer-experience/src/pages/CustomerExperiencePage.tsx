import { useState } from "react";
import { FileText, QrCode, Users } from "lucide-react";
import { ParticipantsPanel } from "./ParticipantsPanel";
import { FormsPanel } from "./FormsPanel";

type Tab = "participants" | "forms";

export function CustomerExperiencePage() {
  const [tab, setTab] = useState<Tab>("participants");

  return (
    <div className="cx-page">
      <header className="cx-header">
        <div className="cx-header__icon" aria-hidden="true">
          <QrCode size={28} strokeWidth={1.75} />
        </div>
        <div>
          <h1 className="cx-header__title">Experiência do Cliente</h1>
          <p className="cx-header__subtitle">
            Gerencie o agradecimento da visita e os formulários personalizáveis do programa.
          </p>
        </div>
      </header>

      <nav className="cx-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "participants"}
          className={`cx-tab ${tab === "participants" ? "is-active" : ""}`}
          onClick={() => setTab("participants")}
        >
          <Users size={16} /> Agradecimento
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "forms"}
          className={`cx-tab ${tab === "forms" ? "is-active" : ""}`}
          onClick={() => setTab("forms")}
        >
          <FileText size={16} /> Formulários
        </button>
      </nav>

      {tab === "participants" ? <ParticipantsPanel /> : <FormsPanel />}
    </div>
  );
}
