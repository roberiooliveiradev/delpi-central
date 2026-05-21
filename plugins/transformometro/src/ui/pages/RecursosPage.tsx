import { useCallback, useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { useSimulatedLoadingProgress } from "../../hooks/useSimulatedLoadingProgress";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createRecurso,
  deleteRecurso,
  fetchOptions,
  fetchRecursos,
  updateRecurso,
  type OptionsData,
  type RecursoCompartilhado,
} from "../../data/api/transformometroApi";
import { labelCriterioRateio } from "../../utils/catalogLabels";
import { toDateInputValue } from "../../utils/dateInputs";
import { formatCurrency } from "../../utils/format";
import { RecursoCatalogFormFields } from "../recursos/RecursoCatalogFormFields";
import {
  emptyRecursoForm,
  payloadFromRecursoForm,
  recursoFormFromEntity,
} from "../recursos/recursoCatalogForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function RecursosPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [items, setItems] = useState<RecursoCompartilhado[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyRecursoForm);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchRecursos(getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar recursos");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = searchQ.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (r) =>
        r.nome_recurso.toLowerCase().includes(q) ||
        r.codigo_recurso.toLowerCase().includes(q) ||
        (r.fornecedor ?? "").toLowerCase().includes(q) ||
        (r.categoria_recurso ?? "").toLowerCase().includes(q)
    );
  }, [items, searchQ]);

  function startCreate() {
    setEditingId(null);
    setForm(emptyRecursoForm());
    setShowForm(true);
  }

  function startEdit(r: RecursoCompartilhado) {
    setEditingId(r.recurso_compartilhado_id);
    setForm(recursoFormFromEntity(r));
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyRecursoForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = payloadFromRecursoForm(form);
    try {
      if (editingId) {
        await updateRecurso(editingId, payload, getAccessToken);
      } else {
        await createRecurso(payload, getAccessToken);
      }
      cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar recurso");
    }
  }

  async function handleDelete(r: RecursoCompartilhado) {
    if (!window.confirm(`Excluir ${r.codigo_recurso} — ${r.nome_recurso}?`)) return;
    setError(null);
    try {
      await deleteRecurso(r.recurso_compartilhado_id, getAccessToken);
      if (editingId === r.recurso_compartilhado_id) cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir recurso");
    }
  }

  const catalogLoadingProgress = useSimulatedLoadingProgress(loading && !options);

  if (loading && !options) {
    return (
      <LoadingActivityCard
        title="Carregando catálogo de recursos"
        description="Licenças, assinaturas e ferramentas compartilhadas."
        progressPercent={catalogLoadingProgress}
      />
    );
  }

  return (
    <div className="dashboard-transformometro dashboard-page">
      <PageHeader
        title="Recursos compartilhados"
        subtitle="Catálogo global — vincule às revisões em Processos para rateio no dashboard"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.recursos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-primary-btn" onClick={startCreate}>
            <Plus size={16} />
            Novo recurso
          </button>
        }
      />

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      <p className="ds-hint">
        Recursos cadastrados aqui aparecem ao vincular em{" "}
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
        >
          Processos → revisão → aba Recursos
        </button>
        .
      </p>

      <section className="ds-card ds-table-section">
        <div className="ds-table-toolbar">
          <label className="ds-table-search">
            <span className="ds-table-search__label">Buscar</span>
            <input
              className="ds-table-search__input"
              placeholder="Código, nome, fornecedor…"
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
            />
          </label>
          <span className="ds-table-section__meta">{filtered.length} recurso(s)</span>
        </div>

        {filtered.length === 0 ? (
          <p className="ds-state-box">
            Nenhum recurso no catálogo. Cadastre licenças e ferramentas compartilhadas.
          </p>
        ) : (
          <div className="ds-table-wrap">
            <table className="ds-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Nome</th>
                  <th>Custo/mês</th>
                  <th>Rateio</th>
                  <th>Status</th>
                  <th>Vigência</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.recurso_compartilhado_id}>
                    <td>{r.codigo_recurso}</td>
                    <td>
                      <strong>{r.nome_recurso}</strong>
                      {r.fornecedor ? (
                        <span className="ds-table__sub"> · {r.fornecedor}</span>
                      ) : null}
                    </td>
                    <td>{formatCurrency(r.valor_total_recorrente)}</td>
                    <td>{labelCriterioRateio(r.criterio_rateio)}</td>
                    <td>{r.status_recurso}</td>
                    <td>
                      {toDateInputValue(r.data_inicio_vigencia) || "…"} →{" "}
                      {toDateInputValue(r.data_fim_vigencia) || "…"}
                    </td>
                    <td className="ds-table__actions">
                      <button type="button" className="ds-ghost-btn" onClick={() => startEdit(r)}>
                        Editar
                      </button>
                      <button
                        type="button"
                        className="ds-ghost-btn"
                        onClick={() => void handleDelete(r)}
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showForm && options ? (
        <section className="ds-card ds-cadastro-subsection">
          <h2 className="ds-section-title">
            {editingId ? "Editar recurso" : "Novo recurso no catálogo"}
          </h2>
          <form onSubmit={handleSubmit}>
            <RecursoCatalogFormFields
              form={form}
              options={options}
              onChange={setForm}
              submitLabel={editingId ? "Salvar alterações" : "Cadastrar recurso"}
            />
            <button
              type="button"
              className="ds-ghost-btn"
              style={{ marginTop: 8 }}
              onClick={cancelForm}
            >
              Cancelar
            </button>
          </form>
        </section>
      ) : null}
    </div>
  );
}
