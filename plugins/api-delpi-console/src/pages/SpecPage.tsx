import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { fetchOpenApiSpec } from "../api/httpClient";
import { API_DELPI_OPENAPI_URL } from "../constants/routes";
import { groupOperationsByTag, parseOpenApiOperations, summarizeOpenApiSpec } from "../lib/openapi";

type Props = {
  onNavigate: (path: string) => void;
};

export function SpecPage({ onNavigate }: Props) {
  const [spec, setSpec] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tagFilter, setTagFilter] = useState("");

  const loadSpec = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOpenApiSpec();
      setSpec(data);
    } catch (e) {
      setSpec(null);
      setError(e instanceof Error ? e.message : "Erro ao carregar especificação");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSpec();
  }, [loadSpec]);

  const summary = useMemo(() => (spec ? summarizeOpenApiSpec(spec) : null), [spec]);
  const operations = useMemo(() => (spec ? parseOpenApiOperations(spec) : []), [spec]);
  const grouped = useMemo(() => {
    const q = tagFilter.trim().toLowerCase();
    const filtered = q
      ? operations.filter(
          (op) =>
            op.tags.some((t) => t.toLowerCase().includes(q)) ||
            op.path.toLowerCase().includes(q),
        )
      : operations;
    return groupOperationsByTag(filtered);
  }, [operations, tagFilter]);

  const downloadSpec = () => {
    if (!spec) return;
    const blob = new Blob([JSON.stringify(spec, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "api-delpi-openapi.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Especificação OpenAPI</h1>
          <p className="adc-subtitle">
            Metadados e inventário de rotas a partir de{" "}
            <code>{API_DELPI_OPENAPI_URL}</code>
          </p>
        </div>
        <div className="adc-header__actions">
          <button type="button" className="adc-btn adc-btn--ghost" onClick={() => void loadSpec()}>
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={downloadSpec}
            disabled={!spec}
          >
            <Download size={16} />
            Baixar JSON
          </button>
        </div>
      </header>

      {loading ? (
        <div className="adc-panel adc-muted">Carregando OpenAPI…</div>
      ) : error ? (
        <div className="adc-panel adc-error">{error}</div>
      ) : summary ? (
        <>
          <section className="adc-metrics adc-metrics--grid">
            <div className="adc-stat">
              <span className="adc-stat__label">API</span>
              <strong>{summary.title}</strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">Versão</span>
              <strong>{summary.version}</strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">OpenAPI</span>
              <strong>{summary.openapiVersion}</strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">Operações</span>
              <strong>{summary.operationCount}</strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">Tags</span>
              <strong>{summary.tagCount}</strong>
            </div>
          </section>

          <input
            className="adc-input"
            type="search"
            placeholder="Filtrar por tag ou path…"
            value={tagFilter}
            onChange={(e) => setTagFilter(e.target.value)}
          />

          <div className="adc-spec-tags">
            {[...grouped.entries()].map(([tag, ops]) => (
              <details key={tag} className="adc-spec-tag" open={grouped.size <= 8}>
                <summary>
                  {tag} <span className="adc-muted">({ops.length})</span>
                </summary>
                <ul>
                  {ops.map((op) => (
                    <li key={op.id}>
                      <span className={`adc-method adc-method--${op.method.toLowerCase()}`}>
                        {op.method}
                      </span>{" "}
                      <code>{op.path}</code>
                      {op.summary ? <span className="adc-muted"> — {op.summary}</span> : null}
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
