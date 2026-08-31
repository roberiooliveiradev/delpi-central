import { ClipboardList, ExternalLink } from "lucide-react";

import { MaintenanceActionButton, MaintenancePageHero } from "../../app/maintenanceUi";
import { MaintenanceScreenLoadingState } from "../../components/MaintenanceLoadingState";
import { StateBox } from "../../components/data";
import { ManutencaoGeralFormEmbed } from "../../components/ManutencaoGeralFormEmbed";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import {
  resolveManutencaoGeralFormUrl,
  shouldOpenManutencaoGeralInNewTab,
  type HostAppRoute,
} from "../../utils/manutencaoGeralFormUrl";
import { resolveMaintenanceHomePath } from "../../utils/routeParser";

type ManutencaoGeralPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  alternateEntry?: string;
  appRoutes?: HostAppRoute[];
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
  appRoutes,
  onNavigate,
}: ManutencaoGeralPageProps) {
  const { submodules, activeFilial, loading: scopeLoading } = useMaintenanceActiveFilial(
    getAccessToken,
    filialScope,
  );
  const effectiveFilial = filialScope ?? activeFilial ?? "01";
  const canAccess = submodules.some((item) => item.id === "manutencao-geral");
  const openInNewTab = shouldOpenManutencaoGeralInNewTab(appRoutes);
  const formUrl = resolveManutencaoGeralFormUrl({
    alternateEntry,
    hostRoutes: appRoutes,
  });
  const homePath = resolveMaintenanceHomePath(filialScope ?? effectiveFilial);

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

  if (!formUrl) {
    return (
      <>
        <ManutencaoGeralHero />
        <section className="dm-page-stack">
          <StateBox variant="error">
            URL do formulário não configurada. Defina <code>routes[].entry</code> no manifesto de
            Manutenção (Admin) e salve; o portal envia o link vivo ao módulo.
          </StateBox>
        </section>
      </>
    );
  }

  if (openInNewTab) {
    return (
      <>
        <ManutencaoGeralHero />
        <section className="dm-page-stack">
          <StateBox>
            <p>
              O formulário de Manutenção geral abre em uma nova aba do navegador.
            </p>
            <p className="dm-home-section__hint">
              Pelo hub, o atalho já abre a aba externa com o Entry atual do manifesto.
            </p>
            <div className="dm-form-embed__actions">
              <MaintenanceActionButton
                type="button"
                variant="primary"
                onClick={() => window.open(formUrl, "_blank", "noopener,noreferrer")}
              >
                <ExternalLink size={16} aria-hidden />
                Abrir formulário
              </MaintenanceActionButton>
              <MaintenanceActionButton
                type="button"
                variant="ghost"
                onClick={() => onNavigate(homePath)}
              >
                Voltar ao início
              </MaintenanceActionButton>
            </div>
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
