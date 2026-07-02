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
import { useScrollToRef } from "../../hooks/useScrollToRef";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createFilial,
  deleteFilial,
  fetchFiliais,
  fetchOptions,
  updateFilial,
  type Filial,
  type OptionsData,
} from "../../data/api/transformometroApi";
import { FilialFormFields } from "../filiais/FilialFormFields";
import {
  emptyFilialForm,
  filialFormFromEntity,
  payloadFromFilialForm,
} from "../filiais/filialCatalogForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function FiliaisPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [items, setItems] = useState<Filial[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyFilialForm);
  const [includeInactive, setIncludeInactive] = useState(true);
  const { ref: formSectionRef, scrollToRef: scrollToForm } = useScrollToRef<HTMLElement>();

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchFiliais(getAccessToken, includeInactive),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar unidades");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, includeInactive]);

  useEffect(() => {
    void load();
  }, [load]);

  function startCreate() {
    setEditingId(null);
    setForm(emptyFilialForm());
    setShowForm(true);
    scrollToForm();
  }

  function startEdit(filial: Filial) {
    setEditingId(filial.filial_id);
    setForm(filialFormFromEntity(filial));
    setShowForm(true);
    scrollToForm();
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyFilialForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = payloadFromFilialForm(form, Boolean(editingId));
    try {
      if (editingId) {
        await updateFilial(
          editingId,
          {
            nome_filial: payload.nome_filial,
            status_filial: payload.status_filial,
          },
          getAccessToken
        );
      } else {
        await createFilial(
          {
            codigo_filial: form.codigo_filial.trim(),
            nome_filial: payload.nome_filial,
            status_filial: payload.status_filial,
          },
          getAccessToken
        );
      }
      cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar unidade");
    }
  }

  async function handleDelete(filial: Filial) {
    if (
      !window.confirm(
        `Excluir unidade ${filial.codigo_filial ?? filial.filial_id} — ${filial.nome_filial}?`
      )
    ) {
      return;
    }
    setError(null);
    try {
      await deleteFilial(filial.filial_id, getAccessToken);
      if (editingId === filial.filial_id) cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir unidade");
    }
  }

  const columns: DataTableColumn<Filial>[] = [
    {
      key: "codigo_filial",
      header: "Código",
      sortable: true,
      sortValue: (row) => row.codigo_filial ?? row.filial_id,
      render: (row) => row.codigo_filial ?? row.filial_id,
    },
    {
      key: "nome_filial",
      header: "Unidade",
      sortable: true,
      className: "ds-table__col--wide",
      sortValue: (row) => row.nome_filial,
      render: (row) => <strong>{row.nome_filial}</strong>,
    },
    {
      key: "status_filial",
      header: "Status",
      sortable: true,
      render: (row) => row.status_filial,
    },
    {
      key: "acoes",
      header: "",
      className: "ds-table__actions",
      render: (row) => (
        <>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => {
              event.stopPropagation();
              startEdit(row);
            }}
          >
            Editar
          </button>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => {
              event.stopPropagation();
              void handleDelete(row);
            }}
          >
            Excluir
          </button>
        </>
      ),
    },
  ];

  const catalogFetchProgress = useTrackedSingleFetchProgress(loading && !options);
  const catalogLoadingProgress = useLoadingProgress(loading && !options, catalogFetchProgress);

  if (loading && !options) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando unidades"
          description="Catálogo de unidades operacionais."
          progressPercent={catalogLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
      <PageHeader
        title="Unidades"
        subtitle="Cadastro de unidades — base para instâncias, setores e escopo do dashboard"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.filiais}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-primary-btn" onClick={startCreate}>
            <Plus size={16} />
            Nova unidade
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
        Unidades ativas aparecem nos formulários de{" "}
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.setores)}
        >
          Setores
        </button>{" "}
        e{" "}
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
        >
          Processos
        </button>
        .
      </p>

      {showForm && options ? (
        <section ref={formSectionRef} className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">{editingId ? "Editar unidade" : "Nova unidade"}</h2>
          <form onSubmit={handleSubmit}>
            <FilialFormFields
              form={form}
              options={options}
              editing={Boolean(editingId)}
              onChange={setForm}
            />
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                {editingId ? "Salvar alterações" : "Cadastrar unidade"}
              </button>
              <button type="button" className="ds-ghost-btn" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <DataTableSection
        title="Catálogo de unidades"
        filters={
          <label className="ds-check-label">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            <span>Incluir unidades inativas</span>
          </label>
        }
        columns={columns}
        rows={items}
        rowKey={(row) => row.filial_id}
        loading={loading}
        refreshing={refreshing}
        hideSearch
        pageSize={15}
        emptyMessage="Nenhuma unidade cadastrada. Use Nova unidade para incluir."
        footer={<p className="ds-hint">{items.length} registro(s)</p>}
      />
    </TransformometroShell>
  );
}
