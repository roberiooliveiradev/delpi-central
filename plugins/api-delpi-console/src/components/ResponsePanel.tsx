import type { ApiFetchResult } from "../api/httpClient";

type Props = {
  result: ApiFetchResult | null;
  loading: boolean;
  error: string | null;
};

function highlightMeta(data: unknown): string {
  return JSON.stringify(data, null, 2);
}

export function ResponsePanel({ result, loading, error }: Props) {
  if (loading) {
    return <div className="adc-panel adc-muted">Executando requisição…</div>;
  }

  if (error) {
    return <div className="adc-panel adc-error">{error}</div>;
  }

  if (!result) {
    return (
      <div className="adc-panel adc-muted">
        Selecione uma rota e clique em Executar para ver status, headers e corpo.
      </div>
    );
  }

  const operationId =
    result.headers["x-operation-id"] ?? result.headers["X-Operation-Id"];
  const responseTime =
    result.headers["x-response-time-ms"] ?? result.headers["X-Response-Time-Ms"];
  const envelopeMeta =
    result.data &&
    typeof result.data === "object" &&
    result.data !== null &&
    "meta" in result.data
      ? (result.data as { meta?: unknown }).meta
      : null;

  return (
    <div className="adc-response">
      <div className="adc-metrics">
        <span className={result.ok ? "adc-badge adc-badge--ok" : "adc-badge adc-badge--err"}>
          HTTP {result.status}
        </span>
        <span className="adc-badge">{result.durationMs} ms (cliente)</span>
        {responseTime ? <span className="adc-badge">servidor {responseTime} ms</span> : null}
        {operationId ? <span className="adc-badge adc-badge--id">{operationId}</span> : null}
      </div>

      {envelopeMeta ? (
        <section className="adc-section">
          <h3>meta (envelope)</h3>
          <pre className="adc-pre adc-pre--meta">{highlightMeta(envelopeMeta)}</pre>
        </section>
      ) : null}

      <section className="adc-section">
        <h3>Headers de resposta</h3>
        <pre className="adc-pre">{JSON.stringify(result.headers, null, 2)}</pre>
      </section>

      <section className="adc-section">
        <h3>Corpo</h3>
        <pre className="adc-pre">
          {result.data ? highlightMeta(result.data) : result.rawText || "(vazio)"}
        </pre>
      </section>
    </div>
  );
}
