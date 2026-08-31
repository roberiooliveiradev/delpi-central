import { useMemo } from "react";
import {
  Building2,
  ChevronRight,
  ClipboardList,
  Cpu,
  Hammer,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { MaintenancePageHero } from "../../app/maintenanceUi";
import { StateBox } from "../../components/data";
import { FilialSwitcher } from "../../components/FilialSwitcher";
import { MaintenanceScreenLoadingState } from "../../components/MaintenanceLoadingState";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import {
  resolveFilialDisplayName,
  setStoredFilial,
} from "../../utils/maintenanceFilialSelection";
import {
  tryOpenManifestPathInNewTab,
  type HostAppRoute,
} from "../../utils/manutencaoGeralFormUrl";

type HomePageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  appRoutes?: HostAppRoute[];
  onNavigate: (path: string) => void;
};

const SUBMODULE_ICONS: Record<string, LucideIcon> = {
  hammer: Hammer,
  "clipboard-list": ClipboardList,
  cpu: Cpu,
};

function SubmoduleIcon({ icon }: { icon: string }) {
  const Icon = SUBMODULE_ICONS[icon] ?? Hammer;
  return <Icon size={20} aria-hidden />;
}

export function HomePage({
  getAccessToken,
  filialScope,
  appRoutes,
  onNavigate,
}: HomePageProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    error: optionsError,
    submodules,
    canManageFiliais,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const heroFilialSwitcher =
    !filialLoading && filiais.length > 1 ? (
      <FilialSwitcher
        filiais={filiais.map((filial) => ({
          id: filial.id,
          label: resolveFilialDisplayName(filiais, filial.id),
        }))}
        value={activeFilial ?? filiais[0]?.id ?? ""}
        onChange={(filialId) => {
          setActiveFilial(filialId);
          if (filialScope) {
            onNavigate(MAINTENANCE_ROUTES.filialHome(filialId));
          }
        }}
        compact
      />
    ) : null;

  const subtitle = useMemo(() => {
    if (filiais.length > 1) {
      return "Escolha a filial e um submódulo para continuar.";
    }
    if (activeFilial) {
      return `Submódulos disponíveis para ${resolveFilialDisplayName(filiais, activeFilial)}.`;
    }
    return "Gestão de manutenção industrial — escolha um submódulo para continuar.";
  }, [activeFilial, filiais]);

  const handleOpenSubmodule = (entryPath: string) => {
    if (activeFilial) {
      setStoredFilial(activeFilial);
    }
    if (tryOpenManifestPathInNewTab(entryPath, { hostRoutes: appRoutes })) {
      return;
    }
    onNavigate(entryPath);
  };

  return (
    <>
      <MaintenancePageHero
        eyebrow="DELPI • MANUTENÇÃO"
        title={
          <>
            <Wrench size={28} strokeWidth={1.75} aria-hidden />
            Manutenção
          </>
        }
        description={subtitle}
        actions={heroFilialSwitcher}
      />

      <section className="dm-page-stack">
        <div className="dm-home">
          {filialLoading ? <MaintenanceScreenLoadingState labelKey="home" /> : null}

          {optionsError ? (
            <p className="dm-home-banner dm-home-banner--error" role="alert">
              {optionsError}
            </p>
          ) : null}

          {!filialLoading && !optionsError ? (
            <section className="dm-home-section" aria-label="Entradas do módulo">
              <div className="dm-home-section__header">
                <div>
                  <h2 className="dm-home-section__title">Começar</h2>
                  <p className="dm-home-section__hint">
                    Atalhos disponíveis conforme sua permissão nesta filial.
                  </p>
                </div>
              </div>

              {canManageFiliais || submodules.length > 0 ? (
                <ul className="dm-home-list">
                  {canManageFiliais ? (
                    <li className="dm-home-list__item">
                      <button
                        type="button"
                        className="dm-home-list__link"
                        onClick={() => onNavigate(MAINTENANCE_ROUTES.filiais)}
                      >
                        <span className="dm-home-list__icon" aria-hidden>
                          <Building2 size={20} />
                        </span>
                        <span className="dm-home-list__body">
                          <strong>Filiais</strong>
                          <span>
                            Cadastro de filiais operacionais do módulo.
                          </span>
                        </span>
                        <span className="dm-home-list__meta">
                          <span className="dm-home-pill dm-home-pill--muted">
                            Administração
                          </span>
                          <ChevronRight size={18} aria-hidden />
                        </span>
                      </button>
                    </li>
                  ) : null}

                  {submodules.map((submodule) => (
                    <li key={submodule.id} className="dm-home-list__item">
                      <button
                        type="button"
                        className="dm-home-list__link"
                        onClick={() => handleOpenSubmodule(submodule.entry_path)}
                      >
                        <span className="dm-home-list__icon" aria-hidden>
                          <SubmoduleIcon icon={submodule.icon} />
                        </span>
                        <span className="dm-home-list__body">
                          <strong>{submodule.label}</strong>
                          <span>{submodule.description}</span>
                        </span>
                        <span className="dm-home-list__meta">
                          {activeFilial ? (
                            <span className="dm-home-pill dm-home-pill--info">
                              {resolveFilialDisplayName(filiais, activeFilial)}
                            </span>
                          ) : (
                            <span className="dm-home-pill dm-home-pill--muted">
                              Submódulo
                            </span>
                          )}
                          <ChevronRight size={18} aria-hidden />
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <StateBox>
                  Nenhum submódulo disponível para esta filial. Solicite
                  permissões como{" "}
                  <code>maintenance.mini-applicators.view.filial-XX</code> ou{" "}
                  <code>maintenance.manutencao-geral.view.filial-XX</code>.
                </StateBox>
              )}
            </section>
          ) : null}
        </div>
      </section>
    </>
  );
}
