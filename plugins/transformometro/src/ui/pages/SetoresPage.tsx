import { useCallback, useEffect, useMemo, useState } from "react";
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
  createSetor,
  deleteSetor,
  fetchOptions,
  fetchSetores,
  updateSetor,
  type OptionsData,
  type Setor,
} from "../../data/api/transformometroApi";
import { SetorFormFields } from "../setores/SetorFormFields";
import {
  emptySetorForm,
  payloadFromSetorForm,
  setorFormFromEntity,
} from "../setores/setorCatalogForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function SetoresPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [items, setItems] = useState<Setor[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptySetorForm);
  const [filialFilter, setFilialFilter] = useState("");
  const { ref: formSectionRef, scrollToRef: scrollToForm } = useScrollToRef<HTMLElement>();

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchSetores(getAccessToken, filialFilter || undefined),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar setores");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filialFilter, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const filialLabels = useMemo(() => {
    const map = new Map((options?.filiais ?? []).map((filial) => [filial.id, filial.label]));
    return map;
  }, [options?.filiais]);

  function startCreate() {
    setEditingId(null);
    setForm(emptySetorForm(filialFilter || "01"));
    setShowForm(true);
    scrollToForm();
  }

  function startEdit(setor: Setor) {
    setEditingId(setor.setor_id);
    setForm(setorFormFromEntity(setor));
    setShowForm(true);
    scrollToForm();
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptySetorForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.filiais.length === 0) {
      setError("Selecione ao menos uma filial para o setor.");
      return;
    }
    const payload = payloadFromSetorForm(form, Boolean(editingId));
    try {
      if (editingId) {
        await updateSetor(
          editingId,
          {
            nome_setor: payload.nome_setor,
            filiais: payload.filiais,
            status_setor: payload.status_setor,
          },
          getAccessToken
        );
      } else {
        await createSetor(
          {
            setor_id: form.codigo_setor.trim(),
            nome_setor: payload.nome_setor,
            filiais: payload.filiais,
            status_setor: payload.status_setor,
          },
          getAccessToken
        );
      }
      cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar setor");
    }
  }

  async function handleDelete(setor: Setor) {
    if (!window.confirm(`Excluir setor ${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor}?`)) return;
    setError(null);
    try {
      await deleteSetor(setor.setor_id, getAccessToken);
      if (editingId === setor.setor_id) cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir setor");
    }
  }

  const columns: DataTableColumn<Setor>[] = [
    {
      key: "codigo_setor",
      header: "Código",
      sortable: true,
      sortValue: (row) => row.codigo_setor ?? row.setor_id,
      render: (row) => row.codigo_setor ?? row.setor_id,
    },
    {
      key: "nome_setor",
      header: "Setor",
      sortable: true,
      className: "ds-table__col--wide",
      sortValue: (row) => row.nome_setor,
      render: (row) => <strong>{row.nome_setor}</strong>,
    },
    {
      key: "filiais",
      header: "Filiais",
      render: (row) =>
        (row.filiais ?? [])
          .map((filialId) => `${filialId} — ${filialLabels.get(filialId) ?? filialId}`)
          .join(", ") || "—",
    },
    {
      key: "status_setor",
      header: "Status",
      sortable: true,
      render: (row) => row.status_setor,
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
          title="Carregando setores"
          description="Catálogo de setores vinculados às filiais."
          progressPercent={catalogLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
      <PageHeader
        title="Setores"
        subtitle="Cadastro de setores e vínculo com filiais — usado nos processos"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.setores}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-primary-btn" onClick={startCreate}>
            <Plus size={16} />
            Novo setor
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
        Setores ativos e vinculados à filial aparecem no formulário de{" "}
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
          <h2 className="ds-section-title">{editingId ? "Editar setor" : "Novo setor"}</h2>
          <form onSubmit={handleSubmit}>
            <SetorFormFields
              form={form}
              options={options}
              editing={Boolean(editingId)}
              onChange={setForm}
            />
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                {editingId ? "Salvar alterações" : "Cadastrar setor"}
              </button>
              <button type="button" className="ds-ghost-btn" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <DataTableSection
        title="Catálogo de setores"
        filters={
          <div className="ds-filters-row">
            <div className="ds-filter-box">
              <label htmlFor="tm-setor-list-filial">Filial</label>
              <select
                id="tm-setor-list-filial"
                value={filialFilter}
                onChange={(e) => setFilialFilter(e.target.value)}
              >
                <option value="">Todas</option>
                {(options?.filiais ?? []).map((filial) => (
                  <option key={filial.id} value={filial.id}>
                    {filial.id} — {filial.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        }
        columns={columns}
        rows={items}
        rowKey={(row) => row.setor_id}
        loading={loading}
        refreshing={refreshing}
        hideSearch
        pageSize={15}
        emptyMessage="Nenhum setor cadastrado. Use Novo setor para incluir."
        footer={
          <p className="ds-hint">
            {items.length} registro(s)
            {filialFilter
              ? ` · filtrados para filial ${filialFilter}`
              : ""}
          </p>
        }
      />
    </TransformometroShell>
  );
}
