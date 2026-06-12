import { ClipboardList, ExternalLink } from "lucide-react";

import { StateBox } from "../../components/data";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MANUTENCAO_GERAL_FORM_URL } from "../../constants/manutencaoGeralForm";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";

type ManutencaoGeralPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

export function ManutencaoGeralPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: ManutencaoGeralPageProps) {
  const { submodules, activeFilial } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const effectiveFilial = filialScope ?? activeFilial ?? "01";
  const canAccess = submodules.some((item) => item.id === "manutencao-geral");

  if (!canAccess) {
    return (
      <MaintenanceShell>
        <PageHeader
          title="Manutenção geral"
          subtitle="Formulário de registro de máquinas, equipamentos e lâmpadas."
          icon={ClipboardList}
          currentPath={pathname}
          filialScope={filialScope ?? effectiveFilial}
          onNavigate={onNavigate}
        />
        <StateBox variant="error">
          Acesso restrito para a filial {effectiveFilial}. Solicite{" "}
          <code>maintenance.manutencao-geral.view.filial-01</code>.
        </StateBox>
      </MaintenanceShell>
    );
  }

  return (
    <MaintenanceShell>
      <PageHeader
        title="Manutenção geral"
        subtitle="Registre ocorrências de máquinas, equipamentos, lâmpadas e demais itens."
        icon={ClipboardList}
        currentPath={pathname}
        filialScope={filialScope}
        onNavigate={onNavigate}
      />

      <section className="dm-card dm-external-form-card">
        <div className="dm-external-form-card__icon" aria-hidden="true">
          <ClipboardList size={40} strokeWidth={1.5} />
        </div>
        <h2 className="dm-external-form-card__title">Formulário Google Sheets</h2>
        <p className="dm-external-form-card__text">
          O Google Apps Script não permite exibir este formulário dentro do portal (
          <code>X-Frame-Options: sameorigin</code>). Abra em uma nova aba para registrar a
          ocorrência.
        </p>
        <div className="dm-external-form-card__actions">
          <a
            className="dm-primary-btn"
            href={MANUTENCAO_GERAL_FORM_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={16} />
            Abrir formulário
          </a>
        </div>
        <p className="dm-external-form-card__hint">
          Os registros continuam sendo salvos na planilha configurada no Apps Script.
        </p>
      </section>
    </MaintenanceShell>
  );
}
