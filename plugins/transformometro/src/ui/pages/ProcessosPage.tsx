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
  type OptionsData,
  type Processo,
} from "../../data/api/transformometroApi";
import { FieldLabel } from "../../components/HelpTooltip";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { useScrollToRef } from "../../hooks/useScrollToRef";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { computeProcessoMasterCompletion } from "../../utils/processoCompletion";

const C = TM_HELP_TOOLTIPS.columns;
const P = TM_HELP_TOOLTIPS.processos;
import { ProcessoFormFields } from "../processos/ProcessoFormFields";
import {
  emptyProcessoForm,
  masterPayloadFromProcessoForm,
  type ProcessoFormState,
} from "../processos/processoForm";
import { renderTableStatus } from "../../utils/tablePresentation";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  onOpenProcesso: (id: string, options?: { setupInstancia?: boolean }) => void;
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
  const [form, setForm] = useState<ProcessoFormState>(emptyProcessoForm);
  const { ref: formSectionRef, scrollToRef: scrollToForm } = useScrollToRef<HTMLElement>();
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQ, setSearchQ] = useState("");

  const listParams = useMemo(() => {
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    if (searchQ.trim()) params.q = searchQ.trim();
    return params;
  }, [searchQ, statusFilter]);

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
    setForm(emptyProcessoForm());
    setShowForm(true);
    scrollToForm();
  }

  function cancelForm() {
    setShowForm(false);
    setForm(emptyProcessoForm());
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload = masterPayloadFromProcessoForm(form);
    try {
      const created = await createProcesso(payload, getAccessToken);
      cancelForm();
      await load();
      onOpenProcesso(created.processo_id, { setupInstancia: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar processo");
    }
  }

  async function handleDuplicate(row: Processo) {
    const label = `${row.codigo_processo} — ${row.nome_processo}`;
    if (
      !window.confirm(
        `Duplicar ${label}? Serão copiados diagrama, mapeamento WBS, melhorias, revisões, medições, investimentos, vínculos e evidências.`
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
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir processo");
    }
  }

  const columns = useMemo<DataTableColumn<Processo>[]>(
    () => [
      { key: "codigo", header: "Código", headerHint: P.codigo, render: (row) => row.codigo_processo, sortable: true },
      {
        key: "nome",
        header: "Processo",
        headerHint: P.nome,
        sortable: true,
        className: "ds-table__col--wide",
        render: (row) => row.nome_processo,
      },
      { key: "status", header: "Status", headerHint: C.status, className: "ds-table__col--status", render: (row) => renderTableStatus(row.status_processo), sortable: true },
      {
        key: "preenchimento",
        header: "Preenchimento",
        headerHint: P.preenchimentoLista,
        className: "ds-table__col--progress",
        render: (row) => (
          <ProcessoFormProgress
            compact
            completion={computeProcessoMasterCompletion(row)}
            title={`Preenchimento mestre — ${row.codigo_processo}`}
          />
        ),
      },
      {
        key: "acoes",
        header: "Ações",
        headerHint: C.acoes,
        className: "ds-table__actions-col",
        render: (row) => (
          <TableRowActions>
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
              className="ds-ghost-btn ds-ghost-btn--danger"
              onClick={(event) => {
                event.stopPropagation();
                void handleDelete(row);
              }}
            >
              Excluir
            </button>
          </TableRowActions>
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

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      {showForm && options ? (
        <section ref={formSectionRef} className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Novo processo</h2>
          <p className="ds-hint">
            Cadastre só o mestre aqui. Unidade e departamento entram na primeira instância operacional
            na tela seguinte. Para alterar um processo existente, abra-o e edite o card desejado.
          </p>
          <form onSubmit={handleSubmit}>
            <ProcessoFormFields
              form={form}
              options={options}
              showInstanciaFields={false}
              onChange={setForm}
            />
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">
                Criar processo
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
        hint="Filtros acima aplicam na API · Duplicar/Excluir ou clique na linha para abrir"
        filters={
          <section className="ds-filters-row ds-filters-row--extended">
            <div className="ds-filter-box ds-filter-box--wide">
              <FieldLabel label="Buscar" hint={P.busca} />
              <input
                id="tm-proc-q"
                type="search"
                placeholder="Nome ou código…"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
              />
            </div>
            <SelectField
              id="tm-proc-list-status"
              label="Status"
              hint={P.filtroStatus}
              value={statusFilter}
              onChange={setStatusFilter}
              allowEmpty
              emptyLabel="Todos"
              options={mapSelectOptions(options?.status_processo ?? [])}
            />
          </section>
        }
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
