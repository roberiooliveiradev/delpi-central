import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Plus } from "lucide-react";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createRevisao,
  fetchOptions,
  fetchProcesso,
  fetchProcessoComparativo,
  fetchRevisoes,
  type OptionsData,
  type Processo,
  type RevisionCompareItem,
  type Revisao,
} from "../../data/api/transformometroApi";
import { optionalDateField, todayDateInput, toDateInputValue } from "../../utils/dateInputs";
import {
  badgeClassStatusAprovacao,
  labelStatusAprovacao,
} from "../../utils/revisaoWorkflowLabels";
import { RevisaoCadastroPanel } from "./RevisaoCadastroPanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

export function ProcessoDetailPage({
  getAccessToken,
  processoId,
  pathname,
  onNavigate,
  onBack,
}: Props) {
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showRevisaoForm, setShowRevisaoForm] = useState(false);
  const [selectedRevisaoId, setSelectedRevisaoId] = useState<string | null>(null);
  const [comparativo, setComparativo] = useState<RevisionCompareItem[]>([]);
  const [revForm, setRevForm] = useState({
    versao_revisao: "1.0.0",
    cenario_tipo: "baseline",
    data_inicio_vigencia: todayDateInput(),
    data_implantacao: "",
    data_fim_vigencia: "",
    revisao_ativa: true,
  });

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [proc, revs, opts, comp] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
        fetchProcessoComparativo(processoId, getAccessToken),
      ]);
      setProcesso(proc);
      setRevisoes(revs.items);
      setOptions(opts);
      setComparativo(comp.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreateRevisao(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createRevisao(
        {
          processo_id: processoId,
          versao_revisao: revForm.versao_revisao,
          cenario_tipo: revForm.cenario_tipo,
          data_inicio_vigencia: revForm.data_inicio_vigencia,
          revisao_ativa: revForm.revisao_ativa,
          data_implantacao: optionalDateField(revForm.data_implantacao),
          data_fim_vigencia: optionalDateField(revForm.data_fim_vigencia),
        },
        getAccessToken
      );
      setShowRevisaoForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar revisão");
    }
  }

  const selectedRevisao = revisoes.find((r) => r.revisao_id === selectedRevisaoId);

  if (loading && !processo) {
    return (
      <div className="dashboard-transformometro dashboard-page">
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <LoadingActivityCard
          title="Carregando processo"
          description="Buscando dados do processo e revisões."
        />
      </div>
    );
  }

  if (!processo) {
    return (
      <div className="dashboard-transformometro dashboard-page">
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Processo não encontrado."}</p>
          <button type="button" className="ds-primary-btn" onClick={() => void load()}>
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-transformometro dashboard-page">
      <PageHeader
        title={`${processo.codigo_processo} — ${processo.nome_processo}`}
        subtitle={[
          `Filial ${processo.filial_id}`,
          processo.setor_id,
          processo.status_processo,
          processo.familia_processo ? `família ${processo.familia_processo}` : null,
          processo.agrupador_ferramenta ? processo.agrupador_ferramenta : null,
        ]
          .filter(Boolean)
          .join(" · ")}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <>
            <button type="button" className="ds-ghost-btn" onClick={onBack}>
              <ArrowLeft size={16} />
              Lista
            </button>
            <button
              type="button"
              className="ds-primary-btn"
              onClick={() => setShowRevisaoForm((v) => !v)}
            >
              <Plus size={16} />
              {showRevisaoForm ? "Cancelar" : "Nova revisão"}
            </button>
          </>
        }
      />

      <StatusAlerts
        error={error}
        loading={false}
        hasData
        onRetry={() => void load()}
      />

      {showRevisaoForm && options ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Nova revisão</h2>
          <form onSubmit={handleCreateRevisao}>
            <div className="ds-filters-row">
              <div className="ds-filter-box">
                <label htmlFor="tm-rev-versao">Versão</label>
                <input
                  id="tm-rev-versao"
                  required
                  value={revForm.versao_revisao}
                  onChange={(e) => setRevForm({ ...revForm, versao_revisao: e.target.value })}
                />
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-rev-cenario">Cenário</label>
                <select
                  id="tm-rev-cenario"
                  value={revForm.cenario_tipo}
                  onChange={(e) => setRevForm({ ...revForm, cenario_tipo: e.target.value })}
                >
                  {options.cenario_tipo.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-rev-inicio">Início vigência</label>
                <input
                  id="tm-rev-inicio"
                  type="date"
                  required
                  value={revForm.data_inicio_vigencia}
                  onChange={(e) =>
                    setRevForm({ ...revForm, data_inicio_vigencia: e.target.value })
                  }
                />
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-rev-implantacao">Implantação</label>
                <input
                  id="tm-rev-implantacao"
                  type="date"
                  value={revForm.data_implantacao}
                  onChange={(e) =>
                    setRevForm({ ...revForm, data_implantacao: e.target.value })
                  }
                />
              </div>
              <div className="ds-filter-box">
                <label htmlFor="tm-rev-fim">Fim vigência</label>
                <input
                  id="tm-rev-fim"
                  type="date"
                  value={revForm.data_fim_vigencia}
                  onChange={(e) =>
                    setRevForm({ ...revForm, data_fim_vigencia: e.target.value })
                  }
                />
              </div>
              <div className="ds-filter-box ds-filter-box--checkbox">
                <label htmlFor="tm-rev-ativa">
                  <input
                    id="tm-rev-ativa"
                    type="checkbox"
                    checked={revForm.revisao_ativa}
                    onChange={(e) =>
                      setRevForm({ ...revForm, revisao_ativa: e.target.checked })
                    }
                  />
                  Marcar como revisão ativa
                </label>
              </div>
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                Salvar revisão
              </button>
            </div>
          </form>
        </section>
      ) : null}

      {comparativo.length > 0 ? (
        <section className="ds-card ds-table-section">
          <div className="ds-table-section__header">
            <h2 className="ds-section-title">Comparativo de revisões</h2>
          </div>
          <div className="ds-table-wrap">
            <table className="ds-table">
              <thead>
                <tr>
                  <th>Versão</th>
                  <th>Cenário</th>
                  <th>Ativa</th>
                  <th>Última competência</th>
                  <th>Meses c/ dados</th>
                  <th>Economia bruta</th>
                  <th>Economia líquida</th>
                  <th>Horas/mês</th>
                </tr>
              </thead>
              <tbody>
                {comparativo.map((row) => (
                  <tr key={row.revisao_id}>
                    <td>{row.versao_revisao ?? "—"}</td>
                    <td>{row.cenario_tipo ?? "—"}</td>
                    <td>{row.revisao_ativa ? "sim" : "—"}</td>
                    <td>{row.ultima_competencia ?? "—"}</td>
                    <td>{row.meses_com_dados ?? 0}</td>
                    <td>{row.totais.economia_bruta.toLocaleString("pt-BR")}</td>
                    <td>{row.totais.economia_liquida_mes.toLocaleString("pt-BR")}</td>
                    <td>{row.totais.horas_economizadas_mes.toLocaleString("pt-BR")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="ds-card ds-table-section ds-table-section--interactive">
        <div className="ds-table-section__header">
          <h2 className="ds-section-title">Revisões ({revisoes.length})</h2>
        </div>
        <p className="ds-hint">
          Clique em uma revisão para cadastrar medição, investimentos e recursos compartilhados.
        </p>

        {revisoes.length === 0 ? (
          <p className="ds-state-box">Nenhuma revisão. Cadastre baseline e melhoria para mensurar economia.</p>
        ) : (
          <>
            <div className="ds-table-wrap">
              <table className="ds-table ds-table--clickable">
                <thead>
                  <tr>
                    <th>Versão</th>
                    <th>Cenário</th>
                    <th>Início</th>
                    <th>Implantação</th>
                    <th>Fim</th>
                    <th>Aprovação</th>
                    <th>Ativa</th>
                  </tr>
                </thead>
                <tbody>
                  {revisoes.map((r) => (
                    <tr
                      key={r.revisao_id}
                      className={[
                        "ds-table__row--clickable",
                        selectedRevisaoId === r.revisao_id ? "ds-table__row--selected" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() =>
                        setSelectedRevisaoId((id) =>
                          id === r.revisao_id ? null : r.revisao_id
                        )
                      }
                    >
                      <td>{r.versao_revisao}</td>
                      <td>{r.cenario_tipo}</td>
                      <td>{toDateInputValue(r.data_inicio_vigencia) || "—"}</td>
                      <td>{toDateInputValue(r.data_implantacao) || "—"}</td>
                      <td>{toDateInputValue(r.data_fim_vigencia) || "—"}</td>
                      <td>
                        <span className={badgeClassStatusAprovacao(r.status_aprovacao)}>
                          {labelStatusAprovacao(r.status_aprovacao)}
                        </span>
                      </td>
                      <td>
                        {r.revisao_ativa ? (
                          <span className="ds-badge ds-badge--success">ativa</span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedRevisao && options ? (
              <RevisaoCadastroPanel
                revisao={selectedRevisao}
                options={options}
                getAccessToken={getAccessToken}
                onError={setError}
                onRevisaoUpdated={load}
              />
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
