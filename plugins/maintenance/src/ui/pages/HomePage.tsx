import { useMemo } from "react";
import { Building2, ClipboardList, Hammer, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { StateBox } from "../../components/data";
import { FilialSwitcher } from "../../components/FilialSwitcher";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { setStoredFilial } from "../../utils/maintenanceFilialSelection";

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

function SubmoduleIcon({ icon }: { icon: string }) {
  const Icon = SUBMODULE_ICONS[icon] ?? Hammer;
  return <Icon size={22} />;
}

function filialLabel(filiais: Array<{ id: string; label: string }>, filialId: string | undefined): string {
  if (!filialId) return "";
  const match = filiais.find((item) => item.id === filialId);
  return match ? `${match.id} — ${match.label}` : filialId;
}

export function HomePage({ getAccessToken, pathname, filialScope, onNavigate }: HomePageProps) {
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    error: optionsError,
    submodules,
    canManageMiniApplicators,
  } = useMaintenanceActiveFilial(getAccessToken, filialScope);

  const subtitle = useMemo(() => {
    if (filiais.length > 1) {
      return "Escolha a filial e o submódulo para continuar.";
    }
    if (activeFilial) {
      return `Submódulos disponíveis para a filial ${filialLabel(filiais, activeFilial)}.`;
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

      <section className="dm-kpi-grid">
        {canManageMiniApplicators ? (
          <button
            type="button"
            className="dm-card dm-kpi-card dm-kpi-card--action"
            onClick={() => onNavigate(MAINTENANCE_ROUTES.filiais)}
          >
            <div className="dm-kpi-card__icon" aria-hidden="true">
              <Building2 size={22} />
            </div>
            <div>
              <p className="dm-kpi-card__label">Administração</p>
              <h2 className="dm-kpi-card__value">Filiais</h2>
              <p className="dm-kpi-card__hint">Cadastro de filiais operacionais do módulo.</p>
            </div>
          </button>
        ) : null}
        {submodules.map((submodule) => (
          <button
            key={submodule.id}
            type="button"
            className="dm-card dm-kpi-card dm-kpi-card--action"
            onClick={() => handleOpenSubmodule(submodule.entry_path)}
          >
            <div className="dm-kpi-card__icon" aria-hidden="true">
              <SubmoduleIcon icon={submodule.icon} />
            </div>
            <div>
              <p className="dm-kpi-card__label">Submódulo</p>
              <h2 className="dm-kpi-card__value">{submodule.label}</h2>
              <p className="dm-kpi-card__hint">{submodule.description}</p>
              {activeFilial ? (
                <p className="dm-kpi-card__meta">Filial: {filialLabel(filiais, activeFilial)}</p>
              ) : null}
            </div>
          </button>
        ))}
      </section>

      {optionsError ? <StateBox variant="error">{optionsError}</StateBox> : null}

      {!optionsError && !filialLoading && submodules.length === 0 ? (
        <StateBox>
          Nenhum submódulo disponível. Solicite permissões como{" "}
          <code>maintenance.mini-applicators.view</code> e escopo de filial{" "}
          <code>maintenance.view.filial-XX</code> na Core API.
        </StateBox>
      ) : null}
    </MaintenanceShell>
  );
}
