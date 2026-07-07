import { useEffect, useMemo, useState } from "react";
import { FileText, QrCode, Users } from "lucide-react";
import {
  formsListPath,
  parseRoute,
  participantsPath,
  type CxTab,
} from "../constants/routes";
import { CxPermissionsProvider, useCxPermissions } from "../context/CxPermissionsContext";
import { navigateCx } from "../utils/navigation";
import { ParticipantsPanel } from "./ParticipantsPanel";
import { FormsPanel } from "./FormsPanel";

type Props = {
  pathname?: string;
};

function CustomerExperienceShell({ pathname }: Props) {
  const { loading, canReadParticipants, canReadForms } = useCxPermissions();
  const route = useMemo(() => parseRoute(pathname), [pathname]);
  const [tab, setTab] = useState<CxTab>(route.tab);

  useEffect(() => {
    setTab(route.tab);
  }, [route.tab]);

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

  const handleTabChange = (next: CxTab) => {
    if (next === "participants") {
      navigateCx(participantsPath());
      return;
    }
    navigateCx(formsListPath());
  };

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
              onClick={() => handleTabChange("participants")}
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
              onClick={() => handleTabChange("forms")}
            >
              <FileText size={16} /> Formulários
            </button>
          )}
        </nav>
      )}

      {tab === "participants" && canReadParticipants ? <ParticipantsPanel /> : null}
      {tab === "forms" && canReadForms ? (
        <FormsPanel
          view={route.formsView}
          formId={route.formId}
          onNavigate={navigateCx}
        />
      ) : null}
    </div>
  );
}

export function CustomerExperiencePage({ pathname }: Props) {
  return (
    <CxPermissionsProvider>
      <CustomerExperienceShell pathname={pathname} />
    </CxPermissionsProvider>
  );
}
