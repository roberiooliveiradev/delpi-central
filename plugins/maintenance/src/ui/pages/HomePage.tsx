import { useMemo } from "react";
import { Building2, ClipboardList, Hammer, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  NavigationCard,
  navigationCardBemClasses,
} from "@delpi/plugin-ui/index";

import { StateBox } from "../../components/data";
import { FilialSwitcher } from "../../components/FilialSwitcher";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { resolveFilialDisplayName, setStoredFilial } from "../../utils/maintenanceFilialSelection";

type HomePageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

const SUBMODULE_ICONS: Record<string, LucideIcon> = {
  hammer: Hammer,
  "clipboard-list": ClipboardList,
};

const navigationCardClasses = navigationCardBemClasses("dm");

function SubmoduleIcon({ icon }: { icon: string }) {
  const Icon = SUBMODULE_ICONS[icon] ?? Hammer;
  return <Icon size={22} />;
}

export function HomePage({ getAccessToken, pathname, filialScope, onNavigate }: HomePageProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    error: optionsError,
    submodules,
    canManageFiliais,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const subtitle = useMemo(() => {
    if (filiais.length > 1) {
      return "Escolha a filial e o submódulo para continuar.";
    }
    if (activeFilial) {
      return `Submódulos disponíveis para a filial ${resolveFilialDisplayName(filiais, activeFilial)}.`;
    }
    return "Gestão de manutenção industrial — escolha um submódulo para continuar.";
  }, [activeFilial, filiais]);

  const handleFilialChange = (filialId: string) => {
    setActiveFilial(filialId);
    onNavigate(MAINTENANCE_ROUTES.filialHome(filialId));
  };

  const handleOpenSubmodule = (entryPath: string) => {
    if (activeFilial) {
      setStoredFilial(activeFilial);
    }
    onNavigate(entryPath);
  };

  return (
    <MaintenanceShell>
      <PageHeader
        title="Manutenção"
        subtitle={subtitle}
        icon={Wrench}
        currentPath={pathname}
        filialScope={filialScope ?? activeFilial}
        onNavigate={onNavigate}
        showNav={false}
      />

      {!filialLoading && filiais.length > 1 ? (
        <FilialSwitcher
          filiais={filiais}
          value={activeFilial ?? filiais[0]?.id ?? ""}
          onChange={handleFilialChange}
        />
      ) : null}

      <section className="dm-shortcut-grid" aria-label="Atalhos do módulo">
        {canManageFiliais ? (
          <NavigationCard
            classNames={navigationCardClasses}
            orientation="horizontal"
            icon={<Building2 size={22} />}
            eyebrow="Administração"
            title="Filiais"
            description="Cadastro de filiais operacionais do módulo."
            onClick={() => onNavigate(MAINTENANCE_ROUTES.filiais)}
          />
        ) : null}
        {submodules.map((submodule) => (
          <NavigationCard
            key={submodule.id}
            classNames={navigationCardClasses}
            orientation="horizontal"
            icon={<SubmoduleIcon icon={submodule.icon} />}
            eyebrow="Submódulo"
            title={submodule.label}
            description={submodule.description}
            meta={
              activeFilial
                ? `Filial: ${resolveFilialDisplayName(filiais, activeFilial)}`
                : undefined
            }
            onClick={() => handleOpenSubmodule(submodule.entry_path)}
          />
        ))}
      </section>

      {optionsError ? <StateBox variant="error">{optionsError}</StateBox> : null}

      {!optionsError && !filialLoading && submodules.length === 0 ? (
        <StateBox>
          Nenhum submódulo disponível para esta filial. Solicite permissões como{" "}
          <code>maintenance.mini-applicators.view.filial-XX</code> ou{" "}
          <code>maintenance.manutencao-geral.view.filial-XX</code>.
        </StateBox>
      ) : null}
    </MaintenanceShell>
  );
}
