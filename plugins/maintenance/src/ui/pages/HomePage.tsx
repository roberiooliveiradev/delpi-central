import { useEffect, useState } from "react";
import { Hammer, Home, Wrench } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { fetchModuleHealthRaw } from "../../data/api/maintenanceHealthApi";

type HomePageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function HomePage({ getAccessToken, pathname, onNavigate }: HomePageProps) {
  const [health, setHealth] = useState<string>("Verificando API…");

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

  return (
    <MaintenanceShell>
      <PageHeader
        title="Manutenção"
        subtitle="Gestão de manutenção industrial — começando por mini-aplicadores."
        icon={Wrench}
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      <section className="dm-kpi-grid">
        <article className="dm-card dm-kpi-card">
          <div className="dm-kpi-card__icon" aria-hidden="true">
            <Hammer size={22} />
          </div>
          <div>
            <p className="dm-kpi-card__label">Primeiro submódulo</p>
            <h2 className="dm-kpi-card__value">Mini-aplicadores</h2>
            <p className="dm-kpi-card__hint">Reposição de peças, golpes e alertas preventivos.</p>
          </div>
        </article>

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

      <section className="dm-card">
        <h3 className="dm-card__title">Atalhos</h3>
        <div className="dm-shortcuts">
          <button
            type="button"
            className="dm-primary-btn"
            onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
          >
            Abrir mini-aplicadores
          </button>
        </div>
      </section>
    </MaintenanceShell>
  );
}
