import { useEffect, useState } from "react";
import { FileText, QrCode, Users } from "lucide-react";
import { CxPermissionsProvider, useCxPermissions } from "../context/CxPermissionsContext";
import { ParticipantsPanel } from "./ParticipantsPanel";
import { FormsPanel } from "./FormsPanel";

type Tab = "participants" | "forms";

function CustomerExperienceShell() {
  const { loading, canReadParticipants, canReadForms } = useCxPermissions();
  const [tab, setTab] = useState<Tab>("participants");

  useEffect(() => {
    if (loading) return;
    setTab((current) => {
      if (current === "participants" && canReadParticipants) return "participants";
      if (current === "forms" && canReadForms) return "forms";
      if (canReadParticipants) return "participants";
      if (canReadForms) return "forms";
      return current;
    });
  }, [loading, canReadParticipants, canReadForms]);

  if (loading) {
    return <p className="cx-state">Carregando permissões...</p>;
  }

  if (!canReadParticipants && !canReadForms) {
    return (
      <p className="cx-state">
        Você não tem permissão para visualizar participantes ou formulários neste módulo.
      </p>
    );
  }

  const showTabs = canReadParticipants && canReadForms;

  return (
    <div className="cx-page">
      <header className="cx-header">
        <div className="cx-header__icon" aria-hidden="true">
          <QrCode size={28} strokeWidth={1.75} />
        </div>
        <div>
          <h1 className="cx-header__title">Experiência do Cliente</h1>
          <p className="cx-header__subtitle">
            Gerencie participantes da visita e formulários personalizáveis do programa.
          </p>
        </div>
      </header>

      {showTabs && (
        <nav className="cx-tabs" role="tablist">
          {canReadParticipants && (
            <button
              type="button"
              role="tab"
              aria-selected={tab === "participants"}
              className={`cx-tab ${tab === "participants" ? "is-active" : ""}`}
              onClick={() => setTab("participants")}
            >
              <Users size={16} /> Participantes
            </button>
          )}
          {canReadForms && (
            <button
              type="button"
              role="tab"
              aria-selected={tab === "forms"}
              className={`cx-tab ${tab === "forms" ? "is-active" : ""}`}
              onClick={() => setTab("forms")}
            >
              <FileText size={16} /> Formulários
            </button>
          )}
        </nav>
      )}

      {tab === "participants" && canReadParticipants ? <ParticipantsPanel /> : null}
      {tab === "forms" && canReadForms ? <FormsPanel /> : null}
    </div>
  );
}

export function CustomerExperiencePage() {
  return (
    <CxPermissionsProvider>
      <CustomerExperienceShell />
    </CxPermissionsProvider>
  );
}
