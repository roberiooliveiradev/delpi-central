import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Plus } from "lucide-react";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
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

  const comparativoColumns = useMemo<DataTableColumn<RevisionCompareItem>[]>(
    () => [
      { key: "versao", header: "Versão", render: (row) => row.versao_revisao ?? "—" },
      { key: "cenario", header: "Cenário", render: (row) => row.cenario_tipo ?? "—" },
      { key: "ativa", header: "Ativa", render: (row) => (row.revisao_ativa ? "sim" : "—") },
      {
        key: "competencia",
        header: "Última competência",
        render: (row) => row.ultima_competencia ?? "—",
      },
      {
        key: "meses",
        header: "Meses c/ dados",
        className: "ds-table__col--numeric",
        render: (row) => row.meses_com_dados ?? 0,
      },
      {
        key: "bruta",
        header: "Economia bruta",
        className: "ds-table__col--numeric",
        render: (row) => row.totais.economia_bruta.toLocaleString("pt-BR"),
      },
      {
        key: "liquida",
        header: "Economia líquida",
        className: "ds-table__col--numeric",
        render: (row) => row.totais.economia_liquida_mes.toLocaleString("pt-BR"),
      },
      {
        key: "horas",
        header: "Horas/mês",
        className: "ds-table__col--numeric",
        render: (row) => row.totais.horas_economizadas_mes.toLocaleString("pt-BR"),
      },
    ],
    []
  );

  const revisaoColumns = useMemo<DataTableColumn<Revisao>[]>(
    () => [
      { key: "versao", header: "Versão", render: (r) => r.versao_revisao },
      { key: "cenario", header: "Cenário", render: (r) => r.cenario_tipo },
      {
        key: "inicio",
        header: "Início",
        render: (r) => toDateInputValue(r.data_inicio_vigencia) || "—",
      },
      {
        key: "impl",
        header: "Implantação",
        render: (r) => toDateInputValue(r.data_implantacao) || "—",
      },
      { key: "fim", header: "Fim", render: (r) => toDateInputValue(r.data_fim_vigencia) || "—" },
      {
        key: "aprovacao",
        header: "Aprovação",
        render: (r) => (
          <span className={badgeClassStatusAprovacao(r.status_aprovacao)}>
            {labelStatusAprovacao(r.status_aprovacao)}
          </span>
        ),
      },
      {
        key: "ativa",
        header: "Ativa",
        render: (r) =>
          r.revisao_ativa ? (
            <span className="ds-badge ds-badge--success">ativa</span>
          ) : (
            "—"
          ),
      },
    ],
    []
  );

  const processFetchProgress = useTrackedSingleFetchProgress(loading && !processo);
  const processLoadingProgress = useLoadingProgress(
    loading && !processo,
    processFetchProgress
  );

  if (loading && !processo) {
    return (
      <TransformometroShell>
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <LoadingActivityCard
          title="Carregando processo"
          description="Buscando dados do processo e revisões."
          progressPercent={processLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  if (!processo) {
    return (
      <TransformometroShell>
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
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
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
        <DataTableSection
          title="Comparativo de revisões"
          columns={comparativoColumns}
          rows={comparativo}
          rowKey={(row) => row.revisao_id}
          hideSearch
          pageSize={10}
          emptyMessage=""
        />
      ) : null}

      <DataTableSection
        title={`Revisões (${revisoes.length})`}
        columns={revisaoColumns}
        rows={revisoes}
        rowKey={(r) => r.revisao_id}
        hideSearch
        pageSize={10}
        emptyMessage="Nenhuma revisão. Cadastre baseline e melhoria para mensurar economia."
        onRowClick={(r) =>
          setSelectedRevisaoId((id) => (id === r.revisao_id ? null : r.revisao_id))
        }
        getRowClassName={(r) =>
          selectedRevisaoId === r.revisao_id ? "ds-table__row--selected" : undefined
        }
        footer={
          <p className="ds-hint">
            Clique em uma revisão para cadastrar medição, investimentos e recursos compartilhados.
          </p>
        }
      />

      {selectedRevisao && options ? (
        <RevisaoCadastroPanel
          revisao={selectedRevisao}
          options={options}
          getAccessToken={getAccessToken}
          onError={setError}
          onRevisaoUpdated={load}
        />
      ) : null}
    </TransformometroShell>
  );
}
