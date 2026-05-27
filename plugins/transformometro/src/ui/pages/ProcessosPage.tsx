import { useCallback, useEffect, useMemo, useState } from "react";
import { Copy, Plus } from "lucide-react";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createProcesso,
  deleteProcesso,
  duplicateProcesso,
  fetchOptions,
  fetchProcessos,
  updateProcesso,
  type OptionsData,
  type Processo,
} from "../../data/api/transformometroApi";
import { ProcessoFormFields } from "../processos/ProcessoFormFields";
import {
  emptyProcessoForm,
  payloadFromProcessoForm,
  processoFormFromEntity,
  type ProcessoFormState,
} from "../processos/processoForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  onOpenProcesso: (id: string) => void;
};

export function ProcessosPage({
  getAccessToken,
  pathname,
  onNavigate,
  onOpenProcesso,
}: Props) {
  const [items, setItems] = useState<Processo[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<ProcessoFormState>(emptyProcessoForm);
  const [filialId, setFilialId] = useState("");
  const [setorId, setSetorId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQ, setSearchQ] = useState("");
  const [familiaFilter, setFamiliaFilter] = useState("");

  const listParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (filialId) params.filial_id = filialId;
    if (setorId) params.setor_id = setorId;
    if (statusFilter) params.status = statusFilter;
    if (searchQ.trim()) params.q = searchQ.trim();
    if (familiaFilter.trim()) params.familia_processo = familiaFilter.trim();
    return params;
  }, [familiaFilter, filialId, searchQ, setorId, statusFilter]);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchProcessos(getAccessToken, listParams),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, listParams]);

  useEffect(() => {
    void load();
  }, [load]);

  function startCreate() {
    setEditingId(null);
    setForm(emptyProcessoForm());
    setShowForm(true);
  }

  function startEdit(row: Processo) {
    setEditingId(row.processo_id);
    setForm(processoFormFromEntity(row));
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyProcessoForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = payloadFromProcessoForm(form);
    try {
      if (editingId) {
        await updateProcesso(editingId, payload, getAccessToken);
        cancelForm();
        await load();
      } else {
        const created = await createProcesso(payload, getAccessToken);
        cancelForm();
        await load();
        onOpenProcesso(created.processo_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar processo");
    }
  }

  async function handleDuplicate(row: Processo) {
    const label = `${row.codigo_processo} — ${row.nome_processo}`;
    if (
      !window.confirm(
        `Duplicar ${label}? Serão copiadas revisões, medições, investimentos e vínculos de recursos.`
      )
    ) {
      return;
    }
    setError(null);
    try {
      const result = await duplicateProcesso(row.processo_id, undefined, getAccessToken);
      await load();
      onOpenProcesso(result.processo.processo_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao duplicar processo");
    }
  }

  async function handleDelete(row: Processo) {
    const label = `${row.codigo_processo} — ${row.nome_processo}`;
    if (!window.confirm(`Excluir o processo ${label}? Revisões e dados vinculados permanecem no banco (exclusão lógica).`)) {
      return;
    }
    setError(null);
    try {
      await deleteProcesso(row.processo_id, getAccessToken);
      if (editingId === row.processo_id) cancelForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir processo");
    }
  }

  const editingRow = editingId ? items.find((p) => p.processo_id === editingId) : null;

  const columns = useMemo<DataTableColumn<Processo>[]>(
    () => [
      { key: "codigo", header: "Código", render: (row) => row.codigo_processo },
      {
        key: "nome",
        header: "Processo",
        className: "ds-table__col--wide",
        render: (row) => row.nome_processo,
      },
      { key: "filial", header: "Filial", render: (row) => row.filial_id },
      { key: "setor", header: "Setor", render: (row) => row.setor_id },
      { key: "familia", header: "Família", render: (row) => row.familia_processo ?? "—" },
      { key: "status", header: "Status", render: (row) => row.status_processo },
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
                void handleDuplicate(row);
              }}
            >
              <Copy size={14} />
              Duplicar
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
    ],
    []
  );

  return (
    <TransformometroShell>
      <PageHeader
        title="Processos"
        subtitle="Cadastro mestre das melhorias monitoradas no PostgreSQL"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button type="button" className="ds-primary-btn" onClick={startCreate}>
            <Plus size={16} />
            Novo processo
          </button>
        }
      />

      <section className="ds-filters-row ds-filters-row--extended">
        <div className="ds-filter-box ds-filter-box--wide">
          <label htmlFor="tm-proc-q">Buscar</label>
          <input
            id="tm-proc-q"
            type="search"
            placeholder="Nome ou código…"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
          />
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-list-filial">Filial</label>
          <select
            id="tm-proc-list-filial"
            value={filialId}
            onChange={(e) => setFilialId(e.target.value)}
          >
            <option value="">Todas</option>
            {(options?.filiais ?? []).map((f) => (
              <option key={f.id} value={f.id}>
                {f.id} — {f.label}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-list-setor">Setor</label>
          <select
            id="tm-proc-list-setor"
            value={setorId}
            onChange={(e) => setSetorId(e.target.value)}
          >
            <option value="">Todos</option>
            {(options?.setores ?? []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-list-status">Status</label>
          <select
            id="tm-proc-list-status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Todos</option>
            {(options?.status_processo ?? []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-list-familia">Família</label>
          <input
            id="tm-proc-list-familia"
            type="search"
            placeholder="ex.: ia"
            value={familiaFilter}
            onChange={(e) => setFamiliaFilter(e.target.value)}
          />
        </div>
      </section>

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      {showForm && options ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">
            {editingId ? "Editar processo" : "Novo processo"}
          </h2>
          <form onSubmit={handleSubmit}>
            <ProcessoFormFields
              form={form}
              options={options}
              codigoProcesso={editingRow?.codigo_processo}
              onChange={setForm}
            />
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                {editingId ? "Salvar alterações" : "Criar processo"}
              </button>
              <button type="button" className="ds-ghost-btn" onClick={cancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      <DataTableSection
        title="Lista de processos"
        hint="Filtros acima aplicam na API · Editar/Excluir ou clique na linha para revisões"
        columns={columns}
        rows={items}
        rowKey={(row) => row.processo_id}
        loading={loading}
        refreshing={refreshing}
        hideSearch
        pageSize={15}
        emptyMessage="Nenhum processo. Use Novo processo para cadastrar."
        onRowClick={(row) => onOpenProcesso(row.processo_id)}
        footer={
          <p className="ds-hint">
            Clique na linha para abrir revisões, medições e investimentos.
          </p>
        }
      />
    </TransformometroShell>
  );
}
