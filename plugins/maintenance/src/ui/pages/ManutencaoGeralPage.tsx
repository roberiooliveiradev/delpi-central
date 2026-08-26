import { ClipboardList } from "lucide-react";

import { MaintenancePageHero } from "../../app/maintenanceUi";
import { MaintenanceScreenLoadingState } from "../../components/MaintenanceLoadingState";
import { StateBox } from "../../components/data";
import { ManutencaoGeralFormEmbed } from "../../components/ManutencaoGeralFormEmbed";
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

const HERO_DESCRIPTION =
  "Formulário de registro de máquinas, equipamentos e lâmpadas.";

function ManutencaoGeralHero({ title = "Manutenção geral" }: { title?: string }) {
  return (
    <MaintenancePageHero
      eyebrow="DELPI • MANUTENÇÃO"
      title={
        <>
          <ClipboardList size={28} strokeWidth={1.75} aria-hidden />
          {title}
        </>
      }
      description={HERO_DESCRIPTION}
    />
  );
}

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
      <>
        <ManutencaoGeralHero />
        <section className="dm-page-stack">
          <MaintenanceScreenLoadingState labelKey="manutencaoGeral" />
        </section>
      </>
    );
  }

  if (!canAccess) {
    return (
      <>
        <ManutencaoGeralHero />
        <section className="dm-page-stack">
          <StateBox variant="error">
            Acesso restrito para a filial {effectiveFilial}. Solicite{" "}
            <code>maintenance.manutencao-geral.view.filial-01</code>.
          </StateBox>
        </section>
      </>
    );
  }

  const formUrl = resolveManutencaoGeralFormUrl(alternateEntry);
  const homePath = resolveMaintenanceHomePath(filialScope ?? effectiveFilial);

  if (!formUrl) {
    return (
      <>
        <ManutencaoGeralHero />
        <section className="dm-page-stack">
          <StateBox variant="error">
            URL do formulário não configurada. Defina <code>routes[].entry</code> no manifesto de
            Manutenção e re-registre o app no portal.
          </StateBox>
        </section>
      </>
    );
  }

  return (
    <section className="dm-page-stack">
      <ManutencaoGeralFormEmbed
        formUrl={formUrl}
        pathname={pathname}
        homePath={homePath}
        onNavigate={onNavigate}
      />
    </section>
  );
}
