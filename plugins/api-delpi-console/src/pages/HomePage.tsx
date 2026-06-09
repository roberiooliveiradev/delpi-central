import { useCallback, useState } from "react";
import {
  Activity,
  Bell,
  BookOpen,
  CheckCircle2,
  Database,
  FileJson,
  ShieldCheck,
  Terminal,
  XCircle,
} from "lucide-react";
import { MONITOR_REFRESH_MS } from "../constants/monitoring";
import { fetchConsoleHealth, type ConsoleHealthPayload } from "../lib/consoleAlerts";
import { fetchHealth, type ApiFetchResult } from "../api/httpClient";
import { usePolling } from "../lib/usePolling";

type Props = {
  onNavigate: (segment: string, searchParams?: Record<string, string | null | undefined>) => void;
};

function statusClass(status: ConsoleHealthPayload["status"] | undefined): string {
  if (status === "critical") return "adc-health__err";
  if (status === "warning") return "adc-health__warn";
  return "adc-health__ok";
}

export function HomePage({ onNavigate }: Props) {
  const [health, setHealth] = useState<ApiFetchResult | null>(null);
  const [consoleHealth, setConsoleHealth] = useState<ConsoleHealthPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [apiHealth, monitorHealth] = await Promise.all([fetchHealth(), fetchConsoleHealth()]);
      setHealth(apiHealth);
      setConsoleHealth(monitorHealth);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao verificar saúde");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(refresh, MONITOR_REFRESH_MS, { immediate: true });

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header">
        <div>
          <h1>Console API DELPI</h1>
          <p className="adc-subtitle">
            Documentação interativa, OpenAPI e monitoramento contínuo da api-delpi (polling 30 s).
          </p>
        </div>
      </header>

      <section className="adc-card-grid">
        <article className="adc-card">
          <div className="adc-card__icon">
            <Activity size={22} />
          </div>
          <h2>Saúde da API</h2>
          {loading && !health ? (
            <p className="adc-muted">Verificando /health…</p>
          ) : error ? (
            <p className="adc-error">{error}</p>
          ) : health ? (
            <div className="adc-health">
              {health.ok ? (
                <CheckCircle2 className="adc-health__ok" size={20} />
              ) : (
                <XCircle className="adc-health__err" size={20} />
              )}
              <span>
                {health.ok ? "Online" : "Indisponível"} — HTTP {health.status} em{" "}
                {health.durationMs} ms
              </span>
            </div>
          ) : null}
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("alertas")}>
          <div className="adc-card__icon">
            <Bell size={22} />
          </div>
          <h2>Monitoramento</h2>
          {consoleHealth ? (
            <div className="adc-health">
              <Activity className={statusClass(consoleHealth.status)} size={20} />
              <span>
                {consoleHealth.status} — {consoleHealth.open_alert_count} alerta(s) · p95{" "}
                {consoleHealth.metrics.p95_ms} ms
              </span>
            </div>
          ) : (
            <p className="adc-muted">Carregando telemetria do console…</p>
          )}
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("documentacao")}>
          <div className="adc-card__icon">
            <BookOpen size={22} />
          </div>
          <h2>Documentação da API</h2>
          <p>Referência interativa de rotas com teste de endpoints e JWT do portal.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("verificacoes")}>
          <div className="adc-card__icon">
            <ShieldCheck size={22} />
          </div>
          <h2>Verificações</h2>
          <p>Smoke suite das rotas críticas — LMP, estoque, qualidade e saúde.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("sql")}>
          <div className="adc-card__icon">
            <Activity size={22} />
          </div>
          <h2>Saúde SQL</h2>
          <p>Top queries por duração e repetição — telemetria do Protheus ao vivo.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("cache")}>
          <div className="adc-card__icon">
            <Database size={22} />
          </div>
          <h2>Cache e callers</h2>
          <p>Hits/miss LMP e estoque, breakdown por caller e comparador de deploy.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("explorer")}>
          <div className="adc-card__icon">
            <Terminal size={22} />
          </div>
          <h2>Explorador de rotas</h2>
          <p>Executa endpoints com params, exemplos do schema e painel de resposta.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("spec")}>
          <div className="adc-card__icon">
            <FileJson size={22} />
          </div>
          <h2>OpenAPI / Spec</h2>
          <p>Inventário por tag, contagem de operações e download do JSON.</p>
        </article>
      </section>

      <section className="adc-panel adc-panel--info">
        <h3>Como funciona o monitoramento</h3>
        <p>
          O console <strong>não usa WebSocket</strong> — ele faz <strong>polling a cada 30 segundos</strong>{" "}
          enquanto a aba está visível. A telemetria SQL e HTTP é alimentada pelo tráfego real na{" "}
          <code>api-delpi</code> (dashboards, smoke, explorador). Alertas críticos podem ir para o{" "}
          <strong>sino da Minha DELPI</strong> (usuários com acesso ao console) e/ou webhook externo.
        </p>
        <p className="adc-muted">
          Roadmap: <code>api-delpi/docs/roadmaps/playbook-api-delpi-console.md</code>
        </p>
      </section>
    </div>
  );
}
