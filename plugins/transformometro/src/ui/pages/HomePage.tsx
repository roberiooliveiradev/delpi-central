import { useEffect, useState } from "react";
import { BarChart3, List, Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { DataSourceBanner } from "../../components/DataSourceBanner";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { ModuleShortcut } from "../../components/ModuleShortcut";
import { PageHeader } from "../../components/PageHeader";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { fetchTransformometroHealth } from "../../data/api/transformometroHealthApi";

type LoadState = "loading" | "ok" | "error";

type HomeProps = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function HomePage({ getAccessToken, pathname, onNavigate }: HomeProps) {
  const [state, setState] = useState<LoadState>("loading");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchTransformometroHealth(getAccessToken)
      .then((payload) => {
        if (cancelled) return;
        setState("ok");
        setDetail(payload as Record<string, unknown>);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState("error");
        setDetail({
          error: error instanceof Error ? error.message : "Erro desconhecido",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  return (
    <div className="dashboard-transformometro dashboard-page">
      <PageHeader
        title="Transformômetro"
        subtitle="Melhorias de processo — economia, investimento, ROI e payback"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
      />

      <DataSourceBanner />

      {state === "loading" ? (
        <LoadingActivityCard
          title="Verificando API"
          description="Conectando ao transformometro-api no portal."
        />
      ) : null}

      {state === "error" ? (
        <div className="ds-state ds-state--error" role="alert">
          <p>Falha ao conectar na API do Transformômetro.</p>
        </div>
      ) : null}

      {state === "ok" && detail ? (
        <section className="ds-card ds-health-card">
          <h2 className="ds-section-title">Status do serviço</h2>
          <dl className="ds-summary-metrics">
            <div className="ds-summary-metric">
              <dt>Módulo</dt>
              <dd>{String(detail.module ?? "—")}</dd>
            </div>
            <div className="ds-summary-metric">
              <dt>Fase</dt>
              <dd>{String(detail.phase ?? "—")}</dd>
            </div>
            <div className="ds-summary-metric">
              <dt>API</dt>
              <dd>{String(detail.status ?? "online")}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      <section className="ds-shortcuts-grid">
        <ModuleShortcut
          title="Dashboard"
          description="KPIs, evolução mensal, ranking e recálculo materializado."
          path={TRANSFORMOMETRO_ROUTES.dashboard}
          onNavigate={onNavigate}
        />
        <ModuleShortcut
          title="Processos"
          description="Cadastro de processos, revisões, medições, investimentos e recursos."
          path={TRANSFORMOMETRO_ROUTES.processos}
          onNavigate={onNavigate}
        />
        <ModuleShortcut
          title="Importar planilha"
          description="Migração Transforma+ (Sheets) com validação e diff do calculador."
          path={TRANSFORMOMETRO_ROUTES.import}
          onNavigate={onNavigate}
        />
      </section>

      <section className="ds-card ds-shortcuts-section">
        <h2 className="ds-section-title">Acesso rápido</h2>
        <div className="ds-header-actions" style={{ marginTop: 0 }}>
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.dashboard)}
          >
            <BarChart3 size={16} />
            Abrir dashboard
          </button>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
          >
            <List size={16} />
            Gerenciar processos
          </button>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.import)}
          >
            <Upload size={16} />
            Importar planilha
          </button>
        </div>
      </section>
    </div>
  );
}
