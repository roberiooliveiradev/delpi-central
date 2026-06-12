import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Search } from "lucide-react";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  deleteVinculo,
  fetchRecurso,
  fetchRecursoVinculos,
  updateVinculo,
  type RecursoCompartilhado,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import { labelBaseCompetencia, labelCriterioRateio, labelEscopoRecurso } from "../../utils/catalogLabels";
import { optionalDateField, toDateInputValue } from "../../utils/dateInputs";
import { formatCurrency } from "../../utils/format";
import { buildProcessoPath } from "../../utils/routeParser";
import { RecursoCustosSection } from "../recursos/RecursoCustosSection";

type Props = Pick<AppProps, "getAccessToken"> & {
  recursoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

type VinculoEditForm = {
  ativo: boolean;
  data_inicio_uso: string;
  data_fim_uso: string;
  peso_rateio: string;
  observacoes: string;
};

type DetailMetricProps = {
  label: string;
  value: string | number;
  highlight?: boolean;
};

function DetailMetric({ label, value, highlight = false }: DetailMetricProps) {
  return (
    <div className="ds-summary-metric">
      <dt>{label}</dt>
      <dd className={highlight ? "ds-summary-metric__value--accent" : undefined}>
        {value}
      </dd>
    </div>
  );
}

function formFromVinculo(vinculo: VinculoRecurso): VinculoEditForm {
  return {
    ativo: Boolean(vinculo.ativo),
    data_inicio_uso: toDateInputValue(vinculo.data_inicio_uso),
    data_fim_uso: toDateInputValue(vinculo.data_fim_uso),
    peso_rateio: vinculo.peso_rateio == null ? "" : String(vinculo.peso_rateio),
    observacoes: vinculo.observacoes ?? "",
  };
}

export function RecursoDetailPage({
  recursoId,
  pathname,
  getAccessToken,
  onNavigate,
  onBack,
}: Props) {
  const [recurso, setRecurso] = useState<RecursoCompartilhado | null>(null);
  const [vinculos, setVinculos] = useState<VinculoRecurso[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<VinculoEditForm | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [recursoData, vinculosData] = await Promise.all([
        fetchRecurso(recursoId, getAccessToken),
        fetchRecursoVinculos(recursoId, getAccessToken),
      ]);
      setRecurso(recursoData);
      setVinculos(vinculosData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar recurso");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, recursoId]);

  useEffect(() => {
    void load();
  }, [load]);

  function startEdit(vinculo: VinculoRecurso) {
    setEditingId(vinculo.vinculo_id);
    setEditForm(formFromVinculo(vinculo));
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm(null);
  }

  async function saveEdit(event: React.FormEvent) {
    event.preventDefault();
    if (!editingId || !editForm) return;

    const peso = editForm.peso_rateio.trim()
      ? Number.parseFloat(editForm.peso_rateio)
      : undefined;
    if (peso != null && (!Number.isFinite(peso) || peso < 0)) {
      setError("Informe um peso de rateio válido.");
      return;
    }

    setError(null);
    try {
      await updateVinculo(
        editingId,
        {
          ativo: editForm.ativo,
          data_inicio_uso: optionalDateField(editForm.data_inicio_uso) ?? undefined,
          data_fim_uso: optionalDateField(editForm.data_fim_uso) ?? undefined,
          peso_rateio: peso,
          observacoes: editForm.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar vínculo");
    }
  }

  async function handleDelete(vinculo: VinculoRecurso) {
    const label = `${vinculo.codigo_processo ?? "processo"} — ${vinculo.nome_processo ?? ""}`;
    if (!window.confirm(`Desvincular este recurso de ${label}?`)) return;
    setError(null);
    try {
      await deleteVinculo(vinculo.vinculo_id, getAccessToken);
      if (editingId === vinculo.vinculo_id) cancelEdit();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao desvincular recurso");
    }
  }

  const ativos = useMemo(() => vinculos.filter((v) => v.ativo).length, [vinculos]);
  const vigenciaRecurso = recurso
    ? `${toDateInputValue(recurso.data_inicio_vigencia) || "…"} → ${toDateInputValue(recurso.data_fim_vigencia) || "…"}`
    : "—";

  const filteredVinculos = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return vinculos;
    return vinculos.filter((row) =>
      [
        row.codigo_processo,
        row.nome_processo,
        row.filial_id,
        row.setor_id,
        row.familia_processo,
        row.versao_revisao,
        row.cenario_tipo,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [search, vinculos]);

  if (loading && !recurso) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando detalhe do recurso"
          description="Buscando cadastro, custos e processos vinculados."
        />
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
      <PageHeader
        title={recurso ? `${recurso.codigo_recurso} — ${recurso.nome_recurso}` : "Recurso"}
        subtitle="Detalhes do recurso, histórico de custos e processos vinculados"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.recursos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-ghost-btn" onClick={onBack}>
            <ArrowLeft size={16} />
            Lista
          </button>
        }
      />

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={Boolean(recurso)}
        onRetry={() => void load()}
      />

      {recurso ? (
        <section className="ds-card ds-cadastro-subsection">
          <div className="ds-table-section__header">
            <h2 className="ds-section-title">Dados do recurso</h2>
            <span className="ds-table-section__meta">{vinculos.length} vínculo(s)</span>
          </div>
          <dl className="ds-summary-metrics ds-summary-metrics--resource-detail">
            <DetailMetric label="Código" value={recurso.codigo_recurso} highlight />
            <DetailMetric label="Status" value={recurso.status_recurso} />
            <DetailMetric label="Categoria" value={recurso.categoria_recurso || "—"} />
            <DetailMetric label="Fornecedor" value={recurso.fornecedor || "—"} />
            <DetailMetric label="Tipo / recorrência" value={`${recurso.tipo_custo} · ${recurso.recorrencia}`} />
            <DetailMetric label="Rateio" value={labelCriterioRateio(recurso.criterio_rateio)} />
            <DetailMetric label="Escopo" value={labelEscopoRecurso(recurso.escopo_recurso)} />
            <DetailMetric
              label="Competência do custo"
              value={labelBaseCompetencia(recurso.base_competencia)}
            />
            <DetailMetric label="Custo mês vigente" value={formatCurrency(recurso.valor_total_recorrente)} highlight />
            <DetailMetric label="Vínculos ativos" value={ativos} highlight />
            <DetailMetric label="Vigência do recurso" value={vigenciaRecurso} />
          </dl>
        </section>
      ) : null}

      <section className="ds-card ds-cadastro-subsection">
        <RecursoCustosSection
          recursoId={recursoId}
          getAccessToken={getAccessToken}
          onError={setError}
          onRecursoSynced={() => void load()}
        />
      </section>

      <section className="ds-card ds-table-section" aria-busy={loading || refreshing}>
        <div className="ds-table-section__header">
          <h2 className="ds-section-title">Processos vinculados</h2>
          <div className="ds-table-section__meta-group">
            <span className="ds-table-section__meta">
              Edite os vínculos ou abra o processo para revisar medição e investimentos
            </span>
            <span className="ds-table-section__meta">{filteredVinculos.length} registro(s)</span>
          </div>
        </div>

        <div className="ds-table-toolbar">
          <div className="ds-table-search" role="search">
            <Search size={16} aria-hidden="true" className="ds-table-search__icon" />
            <input
              type="search"
              className="ds-table-search__input"
              value={search}
              placeholder="Código, processo, filial, setor…"
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Filtrar processos vinculados"
            />
          </div>
        </div>

        {loading && vinculos.length === 0 ? (
          <p className="ds-state-box">Carregando vínculos…</p>
        ) : filteredVinculos.length === 0 ? (
          <p className="ds-state-box">Nenhum processo vinculado a este recurso.</p>
        ) : (
          <div className="ds-table-wrap ds-cadastro-section__table">
            <table className="ds-table ds-table--compact">
              <thead>
                <tr>
                  <th>Processo</th>
                  <th>Filial</th>
                  <th>Setor</th>
                  <th>Revisão</th>
                  <th>Uso no processo</th>
                  <th>Peso</th>
                  <th>Ativo</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filteredVinculos.map((row) =>
                  editingId === row.vinculo_id && editForm ? (
                    <tr key={row.vinculo_id} className="ds-table__row--editing">
                      <td colSpan={8}>
                        <form className="ds-cadastro-subsection" onSubmit={saveEdit}>
                          <h4 className="ds-cadastro-subsection__title">
                            Editar vínculo — {row.codigo_processo ?? "—"} · {row.nome_processo ?? "—"}
                          </h4>
                          <div className="ds-filters-row">
                            <label className="ds-filter-box">
                              Início do uso
                              <input
                                type="date"
                                value={editForm.data_inicio_uso}
                                onChange={(event) =>
                                  setEditForm({ ...editForm, data_inicio_uso: event.target.value })
                                }
                              />
                            </label>
                            <label className="ds-filter-box">
                              Fim do uso
                              <input
                                type="date"
                                value={editForm.data_fim_uso}
                                onChange={(event) =>
                                  setEditForm({ ...editForm, data_fim_uso: event.target.value })
                                }
                              />
                            </label>
                            <label className="ds-filter-box">
                              Peso do rateio
                              <input
                                type="number"
                                min={0}
                                step="any"
                                value={editForm.peso_rateio}
                                onChange={(event) =>
                                  setEditForm({ ...editForm, peso_rateio: event.target.value })
                                }
                              />
                            </label>
                            <label className="ds-filter-box ds-filter-box--checkbox">
                              <span>Vínculo ativo</span>
                              <input
                                type="checkbox"
                                checked={editForm.ativo}
                                onChange={(event) =>
                                  setEditForm({ ...editForm, ativo: event.target.checked })
                                }
                              />
                            </label>
                          </div>
                          <label className="ds-filter-box ds-filter-box--wide">
                            Observações
                            <input
                              value={editForm.observacoes}
                              onChange={(event) =>
                                setEditForm({ ...editForm, observacoes: event.target.value })
                              }
                            />
                          </label>
                          <div className="ds-cadastro-form__actions">
                            <button type="submit" className="ds-primary-btn">
                              Salvar vínculo
                            </button>
                            <button type="button" className="ds-ghost-btn" onClick={cancelEdit}>
                              Cancelar
                            </button>
                          </div>
                        </form>
                      </td>
                    </tr>
                  ) : (
                    <tr key={row.vinculo_id}>
                      <td className="ds-table__col--wide">
                        <button
                          type="button"
                          className="ds-link-btn"
                          onClick={() => {
                            if (row.processo_id) {
                              onNavigate(buildProcessoPath(row.processo_id, row.revisao_id));
                            }
                          }}
                        >
                          {row.codigo_processo ?? "—"} — {row.nome_processo ?? "—"}
                        </button>
                      </td>
                      <td>{row.filial_id ?? "—"}</td>
                      <td>{row.setor_id ?? "—"}</td>
                      <td>
                        {row.versao_revisao ?? "—"} · {row.cenario_tipo ?? "—"}
                      </td>
                      <td>
                        {toDateInputValue(row.data_inicio_uso) || "…"} →{" "}
                        {toDateInputValue(row.data_fim_uso) || "…"}
                      </td>
                      <td className="ds-table__col--numeric">{row.peso_rateio ?? "—"}</td>
                      <td>{row.ativo ? "Sim" : "Não"}</td>
                      <td className="ds-table__actions">
                        <button
                          type="button"
                          className="ds-ghost-btn"
                          onClick={() => startEdit(row)}
                        >
                          Editar vínculo
                        </button>
                        <button
                          type="button"
                          className="ds-ghost-btn"
                          onClick={() => void handleDelete(row)}
                        >
                          Desvincular
                        </button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </TransformometroShell>
  );
}
