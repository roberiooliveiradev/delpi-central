import { ClipboardList, ExternalLink } from "lucide-react";

import { StateBox } from "../../components/data";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import {
  MANUTENCAO_GERAL_FORM_URL,
  manutencaoGeralFormEmbedUrl,
} from "../../constants/manutencaoGeralForm";
import { useMaintenanceActiveFilial, useMaintenanceModuleHomePath } from "../../hooks/useMaintenanceScope";

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
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope);
  const { submodules } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const canAccess = submodules.some((item) => item.id === "manutencao-geral");

  if (!canAccess) {
    return (
      <MaintenanceShell>
        <PageHeader
          title="Manutenção geral"
          subtitle="Formulário de registro de máquinas, equipamentos e lâmpadas."
          icon={ClipboardList}
          currentPath={pathname}
          filialScope={filialScope}
          onNavigate={onNavigate}
        />
        <StateBox variant="error">
          Acesso restrito. Solicite a permissão <code>maintenance.manutencao-geral.view</code>.
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
        actions={
          <a
            className="dm-primary-btn"
            href={MANUTENCAO_GERAL_FORM_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={16} />
            Abrir em nova aba
          </a>
        }
      />

      <section className="dm-card dm-embedded-form-card">
        <p className="dm-embedded-form-card__hint">
          Se o formulário não carregar abaixo, use <strong>Abrir em nova aba</strong> ou volte ao{" "}
          <button type="button" className="dm-inline-link" onClick={() => onNavigate(moduleHomePath)}>
            início do módulo
          </button>
          .
        </p>
        <iframe
          className="dm-embedded-form"
          title="Formulário — Manutenção geral"
          src={manutencaoGeralFormEmbedUrl()}
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          allow="forms *; clipboard-write"
        />
      </section>
    </MaintenanceShell>
  );
}
