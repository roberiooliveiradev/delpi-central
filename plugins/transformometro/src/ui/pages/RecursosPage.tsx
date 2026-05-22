import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

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

  const columns: DataTableColumn<RecursoCompartilhado>[] = [
    { key: "codigo", header: "Código", render: (r) => r.codigo_recurso },
    {
      key: "nome",
      header: "Nome",
      className: "ds-table__col--wide",
      render: (r) => (
        <>
          <strong>{r.nome_recurso}</strong>
          {r.fornecedor ? <span className="ds-table__sub"> · {r.fornecedor}</span> : null}
        </>
      ),
    },
    {
      key: "custo",
      header: "Custo/mês",
      className: "ds-table__col--numeric",
      render: (r) => formatCurrency(r.valor_total_recorrente),
    },
    { key: "rateio", header: "Rateio", render: (r) => labelCriterioRateio(r.criterio_rateio) },
    { key: "status", header: "Status", render: (r) => r.status_recurso },
    {
      key: "vigencia",
      header: "Vigência",
      render: (r) => (
        <>
          {toDateInputValue(r.data_inicio_vigencia) || "…"} →{" "}
          {toDateInputValue(r.data_fim_vigencia) || "…"}
        </>
      ),
    },
    {
      key: "acoes",
      header: "",
      className: "ds-table__actions",
      render: (r) => (
        <>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => {
              event.stopPropagation();
              startEdit(r);
            }}
          >
            Editar
          </button>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => {
              event.stopPropagation();
              void handleDelete(r);
            }}
          >
            Excluir
          </button>
        </>
      ),
    },
  ];

  const catalogFetchProgress = useTrackedSingleFetchProgress(loading && !options);
  const catalogLoadingProgress = useLoadingProgress(
    loading && !options,
    catalogFetchProgress
  );

  if (loading && !options) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando catálogo de recursos"
          description="Licenças, assinaturas e ferramentas compartilhadas."
          progressPercent={catalogLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
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

      <DataTableSection
        title="Catálogo de recursos"
        columns={columns}
        rows={items}
        rowKey={(r) => r.recurso_compartilhado_id}
        loading={loading}
        refreshing={refreshing}
        searchPlaceholder="Código, nome, fornecedor…"
        getSearchText={(r) =>
          [r.codigo_recurso, r.nome_recurso, r.fornecedor, r.categoria_recurso]
            .filter(Boolean)
            .join(" ")
        }
        emptyMessage="Nenhum recurso no catálogo. Cadastre licenças e ferramentas compartilhadas."
      />

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
    </TransformometroShell>
  );
}
