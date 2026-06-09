import { useEffect, useState } from "react";
import { Download, Play, RefreshCw } from "lucide-react";
import {
  downloadSmokeResult,
  listSmokeSuites,
  loadLastSmokeResult,
  resolveSmokeSuites,
  runSmokeSuite,
  type SmokeSuite,
  type SmokeSuiteResult,
} from "../lib/smokeRunner";

type Props = {
  onNavigate: (path: string) => void;
};

export function VerificacoesPage({ onNavigate }: Props) {
  const [suites, setSuites] = useState<SmokeSuite[]>(() => listSmokeSuites());
  const [selectedSuiteId, setSelectedSuiteId] = useState(suites[0]?.id ?? "");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<SmokeSuiteResult | null>(() => loadLastSmokeResult());
  const [error, setError] = useState<string | null>(null);

  const selectedSuite = suites.find((s) => s.id === selectedSuiteId) ?? suites[0];
  const displayResult =
    result && selectedSuite && result.suiteId === selectedSuite.id ? result : null;

  useEffect(() => {
    let cancelled = false;
    void resolveSmokeSuites().then((loaded) => {
      if (cancelled || loaded.length === 0) return;
      setSuites(loaded);
      setSelectedSuiteId((current) =>
        loaded.some((suite) => suite.id === current) ? current : loaded[0].id,
      );
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const runSuite = async () => {
    if (!selectedSuite) return;
    setRunning(true);
    setError(null);
    try {
      const suiteResult = await runSmokeSuite(selectedSuite);
      setResult(suiteResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao executar verificações");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Verificações</h1>
          <p className="adc-subtitle">
            Smoke suites das rotas críticas — status, latência e operation id por chamada.
          </p>
        </div>
      </header>

      <section className="adc-panel adc-panel--toolbar">
        <div className="adc-toolbar">
          <label className="adc-field adc-field--grow">
            <span className="adc-field__label">Suite</span>
            <select
              className="adc-select"
              value={selectedSuite?.id ?? ""}
              onChange={(e) => setSelectedSuiteId(e.target.value)}
              disabled={running}
            >
              {suites.map((suite) => (
                <option key={suite.id} value={suite.id}>
                  {suite.name}
                </option>
              ))}
            </select>
          </label>
          <div className="adc-toolbar__actions">
            <button
              type="button"
              className="adc-btn adc-btn--primary"
              onClick={() => void runSuite()}
              disabled={running || !selectedSuite}
            >
              {running ? <RefreshCw size={16} className="adc-spin" /> : <Play size={16} />}
              {running ? "Executando…" : "Executar suite"}
            </button>
            {displayResult ? (
              <>
                <button
                  type="button"
                  className="adc-btn adc-btn--ghost"
                  onClick={() => displayResult && downloadSmokeResult(displayResult, "csv")}
                  disabled={running}
                >
                  <Download size={16} />
                  Exportar CSV
                </button>
                <button
                  type="button"
                  className="adc-btn adc-btn--ghost"
                  onClick={() => displayResult && downloadSmokeResult(displayResult, "json")}
                  disabled={running}
                >
                  <Download size={16} />
                  Exportar JSON
                </button>
              </>
            ) : null}
          </div>
        </div>
      </section>

      {selectedSuite ? (
        <p className="adc-muted adc-suite-desc">{selectedSuite.description}</p>
      ) : null}

      {error ? <div className="adc-panel adc-panel--danger">{error}</div> : null}

      {displayResult ? (
        <>
          <div className="adc-metrics adc-metrics--grid">
            <div className="adc-stat">
              <span className="adc-stat__label">Passou</span>
              <strong className="adc-ok">{displayResult.passed}</strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">Falhou</span>
              <strong className={displayResult.failed > 0 ? "adc-err" : "adc-muted"}>
                {displayResult.failed}
              </strong>
            </div>
            <div className="adc-stat">
              <span className="adc-stat__label">Duração total</span>
              <strong>{displayResult.totalMs} ms</strong>
            </div>
          </div>

          <div className="adc-table-wrap">
            <table className="adc-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Caso</th>
                  <th>HTTP</th>
                  <th>ms</th>
                  <th>Operation Id</th>
                  <th>Detalhe</th>
                </tr>
              </thead>
              <tbody>
                {displayResult.cases.map((item) => (
                  <tr key={item.caseId}>
                    <td>
                      <span className={item.ok ? "adc-badge adc-badge--ok" : "adc-badge adc-badge--err"}>
                        {item.ok ? "OK" : "Falha"}
                      </span>
                    </td>
                    <td>
                      <div>{item.label}</div>
                      <code className="adc-mono-sm">{item.method} {item.path}</code>
                    </td>
                    <td>{item.status}</td>
                    <td>{item.durationMs}</td>
                    <td>
                      <code className="adc-mono-sm">{item.operationIdHeader ?? "—"}</code>
                    </td>
                    <td className="adc-muted">{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : result && selectedSuite && result.suiteId !== selectedSuite.id ? (
        <div className="adc-panel adc-muted">
          Resultado salvo é da suite «{result.suiteId}». Execute «{selectedSuite.name}» para
          atualizar a tabela.
        </div>
      ) : (
        <div className="adc-panel adc-muted">
          Selecione uma suite e execute para validar rotas críticas após deploy ou mudança de contrato.
        </div>
      )}
    </div>
  );
}
