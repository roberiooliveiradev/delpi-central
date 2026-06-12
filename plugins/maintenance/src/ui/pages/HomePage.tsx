import { useEffect, useMemo, useState } from "react";
import { Hammer, Home, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { StateBox } from "../../components/data";
import { FilialSwitcher } from "../../components/FilialSwitcher";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { useMaintenanceActiveFilial } from "../../hooks/useMaintenanceScope";
import { fetchModuleHealthRaw } from "../../data/api/maintenanceHealthApi";
import { setStoredFilial } from "../../utils/maintenanceFilialSelection";

type HomePageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

const SUBMODULE_ICONS: Record<string, LucideIcon> = {
  hammer: Hammer,
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
  const [health, setHealth] = useState<string>("Verificando API…");
  const {
    filiais,
    activeFilial,
    setActiveFilial,
    loading: filialLoading,
    error: optionsError,
    submodules,
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

  useEffect(() => {
    let active = true;
    fetchModuleHealthRaw(getAccessToken)
      .then((data) => {
        if (!active) return;
        setHealth(
          data.db_ready
            ? `API online — fase ${data.phase}`
            : `API degradada — ${data.db_hint ?? "migrations pendentes"}`,
        );
      })
      .catch((error: Error) => {
        if (!active) return;
        setHealth(error.message);
      });
    return () => {
      active = false;
    };
  }, [getAccessToken]);

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
      />

      {!filialLoading && filiais.length > 1 ? (
        <FilialSwitcher
          filiais={filiais}
          value={activeFilial ?? filiais[0]?.id ?? ""}
          onChange={handleFilialChange}
        />
      ) : null}

      <section className="dm-kpi-grid">
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

        <article className="dm-card dm-kpi-card">
          <div className="dm-kpi-card__icon" aria-hidden="true">
            <Home size={22} />
          </div>
          <div>
            <p className="dm-kpi-card__label">Status da API</p>
            <h2 className="dm-kpi-card__value dm-kpi-card__value--sm">{health}</h2>
            <p className="dm-kpi-card__hint">Monitoramento da API dedicada do módulo.</p>
          </div>
        </article>
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
