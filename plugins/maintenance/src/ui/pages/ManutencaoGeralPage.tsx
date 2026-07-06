import { ClipboardList } from "lucide-react";

import { StateBox } from "../../components/data";
import { ManutencaoGeralFormEmbed } from "../../components/ManutencaoGeralFormEmbed";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { resolveManutencaoGeralFormUrl } from "../../utils/manutencaoGeralFormUrl";
import { resolveMaintenanceHomePath } from "../../utils/routeParser";

type ManutencaoGeralPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  alternateEntry?: string;
  onNavigate: (path: string) => void;
};

export function ManutencaoGeralPage({
  getAccessToken,
  pathname,
  filialScope,
  alternateEntry,
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

  const formUrl = resolveManutencaoGeralFormUrl(alternateEntry);
  const homePath = resolveMaintenanceHomePath(filialScope ?? effectiveFilial);

  if (!formUrl) {
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
          URL do formulário não configurada. Defina <code>routes[].entry</code> no manifesto de
          Manutenção e re-registre o app no portal.
        </StateBox>
      </MaintenanceShell>
    );
  }

  return (
    <MaintenanceShell variant="embed">
      <ManutencaoGeralFormEmbed
        formUrl={formUrl}
        pathname={pathname}
        homePath={homePath}
        onNavigate={onNavigate}
      />
    </MaintenanceShell>
  );
}
