import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import {
  fetchDashboardEvolucao,
  fetchDashboardProcessos,
  fetchDashboardResumo,
  fetchOptions,
  recalcularDashboard,
  type DashboardEvolucaoItem,
  type DashboardProcessoItem,
  type DashboardResumo,
  type OptionsData,
} from "../../data/api/transformometroApi";
import "./ProcessosPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  onGoProcessos?: () => void;
};

function formatBrl(value: number | null | undefined) {
  if (value == null) return "—";
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function DashboardPage({ getAccessToken, onGoProcessos }: Props) {
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [evolucao, setEvolucao] = useState<DashboardEvolucaoItem[]>([]);
  const [processos, setProcessos] = useState<DashboardProcessoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [filialId, setFilialId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculando, setRecalculando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params: Record<string, string> = {};
    if (filialId) params.filial_id = filialId;

    try {
      const [r, ev, proc, opts] = await Promise.all([
        fetchDashboardResumo(getAccessToken, params),
        fetchDashboardEvolucao(getAccessToken, params),
        fetchDashboardProcessos(getAccessToken, params),
        fetchOptions(getAccessToken),
      ]);
      setResumo(r);
      setEvolucao(ev.items);
      setProcessos(proc.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  }, [filialId, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleRecalcular() {
    setRecalculando(true);
    setError(null);
    try {
      await recalcularDashboard(getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recalcular");
    } finally {
      setRecalculando(false);
    }
  }

  return (
    <div className="tm-page">
      <header className="tm-page__header">
        <div>
          <h1>Dashboard</h1>
          <p>Economia bruta e líquida por competência (spec Transformômetro).</p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {onGoProcessos ? (
            <button type="button" className="tm-btn tm-btn--ghost" onClick={onGoProcessos}>
              Processos
            </button>
          ) : null}
          <button
            type="button"
            className="tm-btn tm-btn--primary"
            disabled={recalculando}
            onClick={() => void handleRecalcular()}
          >
            {recalculando ? "Recalculando…" : "Recalcular"}
          </button>
        </div>
      </header>

      {options ? (
        <div className="tm-card tm-form" style={{ marginBottom: "1rem" }}>
          <label>
            Filial
            <select value={filialId} onChange={(e) => setFilialId(e.target.value)}>
              <option value="">Todas</option>
              {options.filiais.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {error ? <div className="tm-alert tm-alert--error">{error}</div> : null}

      {loading ? (
        <p>Carregando indicadores…</p>
      ) : resumo ? (
        <>
          <div className="tm-dashboard-cards">
            <div className="tm-card tm-stat">
              <span className="tm-stat__label">Economia líquida</span>
              <strong>{formatBrl(resumo.economia_liquida_total)}</strong>
            </div>
            <div className="tm-card tm-stat">
              <span className="tm-stat__label">Economia bruta</span>
              <strong>{formatBrl(resumo.economia_bruta_total)}</strong>
            </div>
            <div className="tm-card tm-stat">
              <span className="tm-stat__label">Soluções</span>
              <strong>{resumo.solucoes_implementadas}</strong>
            </div>
            <div className="tm-card tm-stat">
              <span className="tm-stat__label">ROI médio</span>
              <strong>
                {resumo.roi_medio != null
                  ? `${(resumo.roi_medio * 100).toFixed(1)}%`
                  : "—"}
              </strong>
            </div>
          </div>

          <section className="tm-card">
            <h2>Evolução mensal</h2>
            {evolucao.length === 0 ? (
              <p className="tm-muted">Sem dados. Cadastre processos e clique em Recalcular.</p>
            ) : (
              <table className="tm-table tm-table--compact">
                <thead>
                  <tr>
                    <th>Competência</th>
                    <th>Bruta</th>
                    <th>Recorrente</th>
                    <th>Líquida</th>
                  </tr>
                </thead>
                <tbody>
                  {evolucao.map((m) => (
                    <tr key={m.competencia}>
                      <td>{m.competencia}</td>
                      <td>{formatBrl(m.economia_bruta)}</td>
                      <td>{formatBrl(m.custo_recorrente_mes)}</td>
                      <td>{formatBrl(m.economia_liquida_mes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="tm-card">
            <h2>Ranking por processo (mês mais recente)</h2>
            {processos.length === 0 ? (
              <p className="tm-muted">Nenhum processo com economia calculada.</p>
            ) : (
              <table className="tm-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Processo</th>
                    <th>Economia/dia</th>
                    <th>Líquida no mês</th>
                  </tr>
                </thead>
                <tbody>
                  {processos.map((p) => (
                    <tr key={p.processo_id}>
                      <td>{p.codigo_processo}</td>
                      <td>{p.nome_processo}</td>
                      <td>{formatBrl(p.economia_diaria)}</td>
                      <td>{formatBrl(p.economia_liquida_mes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
