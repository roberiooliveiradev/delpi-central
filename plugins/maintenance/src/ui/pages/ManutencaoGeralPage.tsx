import { ClipboardList } from "lucide-react";

import { StateBox } from "../../components/data";
import { ManutencaoGeralFormEmbed } from "../../components/ManutencaoGeralFormEmbed";
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
  const { submodules, activeFilial, loading: scopeLoading } = useMaintenanceActiveFilial(
    getAccessToken,
    filialScope,
  );
  const effectiveFilial = filialScope ?? activeFilial ?? "01";
  const canAccess = submodules.some((item) => item.id === "manutencao-geral");

  if (scopeLoading) {
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
        <StateBox>Carregando…</StateBox>
      </MaintenanceShell>
    );
  }

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
    <MaintenanceShell variant="embed">
      <PageHeader
        title="Manutenção geral"
        subtitle="Registre ocorrências de máquinas, equipamentos, lâmpadas e demais itens."
        icon={ClipboardList}
        currentPath={pathname}
        filialScope={filialScope}
        onNavigate={onNavigate}
      />

      <ManutencaoGeralFormEmbed formUrl={MANUTENCAO_GERAL_FORM_URL} pathname={pathname} />
    </MaintenanceShell>
  );
}
