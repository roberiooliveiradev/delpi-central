import { useCallback, useEffect, useMemo, useState } from "react";
import { ExternalLink, Play, RefreshCw, Search } from "lucide-react";
import { API_DELPI_SWAGGER_URL } from "../constants/routes";
import { apiFetch, fetchOpenApiSpec, type ApiFetchResult } from "../api/httpClient";
import { ResponsePanel } from "../components/ResponsePanel";
import {
  buildPathWithParams,
  groupOperationsByTag,
  parseOpenApiOperations,
  type OpenApiOperation,
} from "../lib/openapi";
import { appendHistory } from "../lib/requestHistory";

type Props = {
  onNavigate: (path: string) => void;
};

export function ExplorerPage({ onNavigate }: Props) {
  const [operations, setOperations] = useState<OpenApiOperation[]>([]);
  const [loadingSpec, setLoadingSpec] = useState(true);
  const [specError, setSpecError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [queryValues, setQueryValues] = useState<Record<string, string>>({});
  const [pathValues, setPathValues] = useState<Record<string, string>>({});
  const [bodyText, setBodyText] = useState("{}");
  const [result, setResult] = useState<ApiFetchResult | null>(null);
  const [executing, setExecuting] = useState(false);
  const [execError, setExecError] = useState<string | null>(null);

  const loadSpec = useCallback(async () => {
    setLoadingSpec(true);
    setSpecError(null);
    try {
      const spec = await fetchOpenApiSpec();
      const ops = parseOpenApiOperations(spec);
      setOperations(ops);
      if (ops.length > 0 && !selectedId) setSelectedId(ops[0].id);
    } catch (e) {
      setSpecError(e instanceof Error ? e.message : "Erro ao carregar OpenAPI");
    } finally {
      setLoadingSpec(false);
    }
  }, [selectedId]);

  useEffect(() => {
    void loadSpec();
  }, [loadSpec]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return operations;
    return operations.filter(
      (op) =>
        op.path.toLowerCase().includes(q) ||
        op.summary.toLowerCase().includes(q) ||
        op.method.toLowerCase().includes(q) ||
        op.tags.some((t) => t.toLowerCase().includes(q)),
    );
  }, [operations, search]);

  const grouped = useMemo(() => groupOperationsByTag(filtered), [filtered]);

  const selected = useMemo(
    () => operations.find((op) => op.id === selectedId) ?? null,
    [operations, selectedId],
  );

  useEffect(() => {
    if (!selected) return;
    const nextQuery: Record<string, string> = {};
    const nextPath: Record<string, string> = {};
    for (const p of selected.parameters) {
      const initial = p.example ?? "";
      if (p.in === "query") nextQuery[p.name] = initial;
      if (p.in === "path") nextPath[p.name] = initial;
    }
    setQueryValues(nextQuery);
    setPathValues(nextPath);
    setBodyText(selected.requestBodyExample ?? "{}");
    setResult(null);
    setExecError(null);
  }, [selected]);

  const execute = async () => {
    if (!selected) return;
    setExecuting(true);
    setExecError(null);
    try {
      const resolvedPath = buildPathWithParams(selected.path, pathValues);
      const query: Record<string, string> = {};
      for (const [k, v] of Object.entries(queryValues)) {
        if (v !== "") query[k] = v;
      }

      let body: unknown = undefined;
      if (selected.hasBody && ["POST", "PUT", "PATCH"].includes(selected.method)) {
        try {
          body = JSON.parse(bodyText);
        } catch {
          setExecError("Corpo JSON inválido");
          setExecuting(false);
          return;
        }
      }

      const response = await apiFetch(resolvedPath, {
        method: selected.method,
        query,
        body,
      });
      setResult(response);
      appendHistory(response, {
        operationId: selected.id,
        path: resolvedPath,
        method: selected.method,
      });
    } catch (e) {
      setExecError(e instanceof Error ? e.message : "Falha na requisição");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="adc-page adc-explorer">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Explorador de rotas</h1>
        </div>
        <div className="adc-header__actions">
          <a
            className="adc-btn adc-btn--ghost"
            href={API_DELPI_SWAGGER_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={16} />
            Swagger
          </a>
          <button type="button" className="adc-btn adc-btn--ghost" onClick={() => void loadSpec()}>
            <RefreshCw size={16} />
            Recarregar OpenAPI
          </button>
        </div>
      </header>

      <div className="adc-explorer__layout">
        <aside className="adc-sidebar">
          <div className="adc-search">
            <Search size={16} />
            <input
              type="search"
              placeholder="Filtrar path, tag, método…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {loadingSpec ? (
            <p className="adc-muted">Carregando especificação…</p>
          ) : specError ? (
            <p className="adc-error">{specError}</p>
          ) : (
            <div className="adc-op-list">
              {[...grouped.entries()].map(([tag, ops]) => (
                <div key={tag} className="adc-op-group">
                  <h3>{tag}</h3>
                  {ops.map((op) => (
                    <button
                      key={op.id}
                      type="button"
                      className={`adc-op-item ${selectedId === op.id ? "adc-op-item--active" : ""}`}
                      onClick={() => setSelectedId(op.id)}
                    >
                      <span className={`adc-method adc-method--${op.method.toLowerCase()}`}>
                        {op.method}
                      </span>
                      <span className="adc-op-item__path">{op.path}</span>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}
        </aside>

        <main className="adc-main">
          {selected ? (
            <>
              <section className="adc-panel">
                <h2>{selected.summary}</h2>
                <p className="adc-muted">
                  <span className={`adc-method adc-method--${selected.method.toLowerCase()}`}>
                    {selected.method}
                  </span>{" "}
                  <code>{selected.path}</code>
                  {selected.deprecated ? " (deprecated)" : ""}
                </p>
                {selected.description ? (
                  <p className="adc-desc">{selected.description}</p>
                ) : null}
                {selected.responseStatuses.length > 0 ? (
                  <div className="adc-responses">
                    <h3>Respostas (OpenAPI)</h3>
                    <ul>
                      {selected.responseStatuses.map((r) => (
                        <li key={r.status}>
                          <strong>{r.status}</strong> — {r.description || "—"}
                          {r.hasExample ? " (exemplo)" : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {selected.parameters.filter((p) => p.in === "path").length > 0 ? (
                  <div className="adc-form-block">
                    <h3>Path params</h3>
                    {selected.parameters
                      .filter((p) => p.in === "path")
                      .map((p) => (
                        <label key={p.name} className="adc-field">
                          <span>
                            {p.name}
                            {p.required ? " *" : ""}
                          </span>
                          <input
                            value={pathValues[p.name] ?? ""}
                            onChange={(e) =>
                              setPathValues((prev) => ({ ...prev, [p.name]: e.target.value }))
                            }
                            placeholder={p.description || p.schemaType}
                          />
                        </label>
                      ))}
                  </div>
                ) : null}

                {selected.parameters.filter((p) => p.in === "query").length > 0 ? (
                  <div className="adc-form-block">
                    <h3>Query params</h3>
                    {selected.parameters
                      .filter((p) => p.in === "query")
                      .map((p) => (
                        <label key={p.name} className="adc-field">
                          <span>
                            {p.name}
                            {p.required ? " *" : ""}
                          </span>
                          <input
                            value={queryValues[p.name] ?? ""}
                            onChange={(e) =>
                              setQueryValues((prev) => ({ ...prev, [p.name]: e.target.value }))
                            }
                            placeholder={p.description || p.schemaType}
                          />
                        </label>
                      ))}
                  </div>
                ) : null}

                {selected.hasBody ? (
                  <div className="adc-form-block">
                    <h3>Corpo (JSON)</h3>
                    <textarea
                      className="adc-textarea"
                      rows={8}
                      value={bodyText}
                      onChange={(e) => setBodyText(e.target.value)}
                    />
                  </div>
                ) : null}

                <button
                  type="button"
                  className="adc-btn adc-btn--primary"
                  onClick={() => void execute()}
                  disabled={executing}
                >
                  <Play size={16} />
                  Executar
                </button>
              </section>

              <ResponsePanel result={result} loading={executing} error={execError} />
            </>
          ) : (
            <div className="adc-panel adc-muted">Nenhuma operação selecionada.</div>
          )}
        </main>
      </div>
    </div>
  );
}
