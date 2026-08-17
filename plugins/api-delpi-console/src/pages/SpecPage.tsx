import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { apiFetch, fetchOpenApiSpec } from "../api/httpClient";
import { API_DELPI_OPENAPI_URL } from "../constants/routes";
import { groupOperationsByTag, parseOpenApiOperations, summarizeOpenApiSpec } from "../lib/openapi";

type OpenApiDiffPayload = {
  added_count: number;
  removed_count: number;
  changed_count: number;
  added: Array<{ method: string; path: string; operationId?: string }>;
  removed: Array<{ method: string; path: string; operationId?: string }>;
  changed: Array<{ method: string; path: string; changes: Record<string, unknown> }>;
};

type EnvelopeContractsPayload = {
  version?: string;
  description?: string;
  routes: Array<{
    method: string;
    path: string;
    operationId: string;
    entity: string;
    shape: string;
  }>;
};

type Props = {
  onNavigate: (path: string) => void;
};

function unwrapEnvelope<T>(data: unknown): T | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as { data?: T };
  return envelope.data ?? (data as T);
}

export function SpecPage({ onNavigate }: Props) {
  const [spec, setSpec] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tagFilter, setTagFilter] = useState("");
  const [diff, setDiff] = useState<OpenApiDiffPayload | null>(null);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [envelopes, setEnvelopes] = useState<EnvelopeContractsPayload | null>(null);
  const [envelopeError, setEnvelopeError] = useState<string | null>(null);
  const [envelopeLoading, setEnvelopeLoading] = useState(false);

  const loadSpec = useCallback(async () => {
    setLoading(true);
    setError(null);
    setDiffError(null);
    setEnvelopeError(null);
    setEnvelopeLoading(true);
    try {
      const [data, diffResponse, envelopeResponse] = await Promise.all([
        fetchOpenApiSpec(),
        apiFetch("/system/openapi-diff"),
        apiFetch("/system/envelope-contracts"),
      ]);
      setSpec(data);
      if (diffResponse.ok) {
        setDiff(unwrapEnvelope<OpenApiDiffPayload>(diffResponse.data));
      } else {
        setDiff(null);
        setDiffError(`Diff indisponível (HTTP ${diffResponse.status})`);
      }
      if (envelopeResponse.ok) {
        setEnvelopes(unwrapEnvelope<EnvelopeContractsPayload>(envelopeResponse.data));
      } else {
        setEnvelopes(null);
        setEnvelopeError(`Envelopes indisponíveis (HTTP ${envelopeResponse.status})`);
      }
    } catch (e) {
      setSpec(null);
      setDiff(null);
      setEnvelopes(null);
      setError(e instanceof Error ? e.message : "Erro ao carregar especificação");
    } finally {
      setLoading(false);
      setEnvelopeLoading(false);
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
          {diff ? (
            <section className="adc-panel">
              <h2 className="adc-section-title">Diff vs baseline versionado</h2>
              <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
                <div className="adc-stat">
                  <span className="adc-stat__label">Adicionadas</span>
                  <strong>{diff.added_count}</strong>
                </div>
                <div className="adc-stat">
                  <span className="adc-stat__label">Removidas</span>
                  <strong>{diff.removed_count}</strong>
                </div>
                <div className="adc-stat">
                  <span className="adc-stat__label">Alteradas</span>
                  <strong>{diff.changed_count}</strong>
                </div>
              </div>
              {diff.added_count + diff.removed_count + diff.changed_count === 0 ? (
                <p className="adc-muted">Nenhuma diferença em relação ao baseline do repositório.</p>
              ) : (
                <ul className="adc-diff-list">
                  {diff.added.map((row) => (
                    <li key={`add-${row.method}-${row.path}`} className="adc-diff-list__item adc-diff-list__item--add">
                      + {row.method} <code>{row.path}</code>
                    </li>
                  ))}
                  {diff.removed.map((row) => (
                    <li key={`rm-${row.method}-${row.path}`} className="adc-diff-list__item adc-diff-list__item--rm">
                      − {row.method} <code>{row.path}</code>
                    </li>
                  ))}
                  {diff.changed.map((row) => (
                    <li key={`chg-${row.method}-${row.path}`} className="adc-diff-list__item adc-diff-list__item--chg">
                      ~ {row.method} <code>{row.path}</code>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}
          {diffError ? <p className="adc-muted">{diffError}</p> : null}

          <section className="adc-panel">
            <h2 className="adc-section-title">Contratos de envelope</h2>
            {envelopeLoading ? (
              <p className="adc-muted">Carregando golden de envelopes…</p>
            ) : envelopeError ? (
              <p className="adc-error">{envelopeError}</p>
            ) : envelopes ? (
              <>
                <p className="adc-muted">
                  {envelopes.description || "Contratos meta.operationId / entity / shape."}
                  {envelopes.version ? ` · versão ${envelopes.version}` : ""}
                </p>
                <div className="adc-table-wrap">
                  <table className="adc-table">
                    <thead>
                      <tr>
                        <th>Método</th>
                        <th>Path</th>
                        <th>operationId</th>
                        <th>entity</th>
                        <th>shape</th>
                      </tr>
                    </thead>
                    <tbody>
                      {envelopes.routes.map((route) => (
                        <tr key={`${route.method}-${route.path}-${route.operationId}`}>
                          <td>
                            <span className={`adc-method adc-method--${route.method.toLowerCase()}`}>
                              {route.method}
                            </span>
                          </td>
                          <td>
                            <code>{route.path}</code>
                          </td>
                          <td>
                            <code>{route.operationId}</code>
                          </td>
                          <td>{route.entity}</td>
                          <td>{route.shape}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="adc-muted">Nenhum contrato de envelope disponível.</p>
            )}
          </section>

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
