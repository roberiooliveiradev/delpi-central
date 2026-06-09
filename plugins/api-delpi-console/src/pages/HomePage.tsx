import { useEffect, useState } from "react";
import { Activity, BookOpen, CheckCircle2, FileJson, Terminal, XCircle } from "lucide-react";
import { fetchHealth, type ApiFetchResult } from "../api/httpClient";

type Props = {
  onNavigate: (path: string) => void;
};

export function HomePage({ onNavigate }: Props) {
  const [health, setHealth] = useState<ApiFetchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchHealth();
        if (!cancelled) setHealth(result);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erro ao verificar saúde");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="adc-page">
      <header className="adc-header">
        <div>
          <h1>Console API DELPI</h1>
          <p className="adc-subtitle">
            Swagger UI, OpenAPI e testes HTTP com inspeção de envelope e latência.
          </p>
        </div>
      </header>

      <section className="adc-card-grid">
        <article className="adc-card">
          <div className="adc-card__icon">
            <Activity size={22} />
          </div>
          <h2>Saúde da API</h2>
          {loading ? (
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

        <article className="adc-card adc-card--action" onClick={() => onNavigate("swagger")}>
          <div className="adc-card__icon">
            <BookOpen size={22} />
          </div>
          <h2>Swagger UI</h2>
          <p>Interface FastAPI com «Try it out» e JWT autorizado automaticamente.</p>
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
        <h3>Integração Swagger</h3>
        <p>
          O Swagger embutido usa <code>/apps/api-delpi/docs</code> com bridge{" "}
          <code>DELPI_AUTH</code> (mesmo contrato do portal para iframes). Em 401, o iframe
          solicita reenvio do token via <code>DELPI_REFRESH_REQUEST</code>.
        </p>
        <p className="adc-muted">
          Roadmap: <code>api-delpi/docs/roadmaps/playbook-api-delpi-console.md</code>
        </p>
      </section>
    </div>
  );
}
